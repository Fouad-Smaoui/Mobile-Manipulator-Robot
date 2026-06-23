#!/usr/bin/env python3
"""Multi-layer, audit-grade verification for Scenario B (Nav2 + SLAM).

Same standard as verify_scenario_c.py: a screenshot or a "Goal accepted"
log line is not evidence. This checks ROS 2 state directly across four
layers and reports PASS/FAIL per layer, not an overall "it works":

  1. SLAM layer    -- slam_toolbox alive, /map publishing with real
                       (non-degenerate) occupancy data.
  2. Nav2 lifecycle -- controller_server, planner_server, behavior_server,
                       bt_navigator all report ACTIVE via the lifecycle
                       service (not just "process running").
  3. TF layer       -- map -> odom -> base_link resolves end-to-end via
                       tf2 lookupTransform, not assumed from launch success.
  4. Navigation     -- sends one real NavigateToPose goal and watches the
                       action's own GoalStatusArray continuously for its
                       *actual* terminal status (SUCCEEDED/ABORTED/
                       CANCELED), not just acceptance. Reports whichever
                       terminal status is actually observed -- including
                       ABORTED, which is a legitimate, informative result
                       when the controller_server's progress_checker
                       correctly detects and reports a stalled approach.

Usage (with gazebo_sim.launch.py, slam_toolbox online_async_launch.py,
and mobile_manipulator_bringup navigation.launch.py already running):
  ros2 run mobile_manipulator_bringup verify_scenario_b.py [--goal-x X --goal-y Y]
"""
import argparse
import sys
import time

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSDurabilityPolicy
from action_msgs.msg import GoalStatus, GoalStatusArray
from nav_msgs.msg import OccupancyGrid
from nav2_msgs.action import NavigateToPose
from lifecycle_msgs.srv import GetState

STATUS_NAMES = {
    0: 'UNKNOWN', 1: 'ACCEPTED', 2: 'EXECUTING', 3: 'CANCELING',
    4: 'SUCCEEDED', 5: 'CANCELED', 6: 'ABORTED',
}
NAV2_LIFECYCLE_NODES = ['controller_server', 'planner_server', 'behavior_server', 'bt_navigator']


class VerifyScenarioB(Node):

    def __init__(self):
        super().__init__('verify_scenario_b')
        self._latest_map = None
        self.create_subscription(OccupancyGrid, '/map', self._on_map, _transient_local_qos())
        self._status_list = []
        self.create_subscription(
            GoalStatusArray, '/navigate_to_pose/_action/status',
            self._on_status, _transient_local_qos(depth=10),
        )
        self._lifecycle_clients = {
            n: self.create_client(GetState, f'/{n}/get_state') for n in NAV2_LIFECYCLE_NODES
        }
        self._nav_client = ActionClient(self, NavigateToPose, '/navigate_to_pose')

    def _on_map(self, msg):
        self._latest_map = msg

    def _on_status(self, msg):
        self._status_list = list(msg.status_list)

    # --- Layer 1: SLAM ------------------------------------------------
    def check_slam_layer(self):
        deadline = time.time() + 10.0
        while self._latest_map is None and time.time() < deadline:
            rclpy.spin_once(self, timeout_sec=0.2)
        if self._latest_map is None:
            return False, 'no /map message received -- slam_toolbox not publishing'
        data = self._latest_map.data
        unknown = sum(1 for v in data if v == -1)
        if unknown == len(data):
            return False, 'map is 100% unknown -- frozen/empty map, no real scan fusion'
        return True, (
            f'/map has {len(data)} cells, {len(data) - unknown} non-unknown '
            f'({self._latest_map.info.width}x{self._latest_map.info.height} @ '
            f'{self._latest_map.info.resolution:.3f} m/cell)'
        )

    # --- Layer 2: Nav2 lifecycle ---------------------------------------
    def check_nav2_lifecycle(self):
        results = {}
        for name, client in self._lifecycle_clients.items():
            if not client.wait_for_service(timeout_sec=8.0):
                results[name] = 'service unavailable'
                continue
            future = client.call_async(GetState.Request())
            rclpy.spin_until_future_complete(self, future, timeout_sec=8.0)
            resp = future.result()
            results[name] = resp.current_state.label if resp else 'no response'
        not_active = {n: s for n, s in results.items() if s != 'active'}
        if not_active:
            return False, f'not all nodes active: {results}'
        return True, f'all 4 nodes active: {results}'

    # --- Layer 3: TF ---------------------------------------------------
    def check_tf_layer(self):
        import tf2_ros
        buf = tf2_ros.Buffer()
        listener = tf2_ros.TransformListener(buf, self)
        deadline = time.time() + 10.0
        last_err = None
        while time.time() < deadline:
            rclpy.spin_once(self, timeout_sec=0.2)
            try:
                t = buf.lookup_transform('map', 'base_link', rclpy.time.Time())
                return True, (
                    f'map->base_link resolves: '
                    f'[{t.transform.translation.x:.3f}, {t.transform.translation.y:.3f}]'
                )
            except Exception as e:
                last_err = str(e)
        return False, f'map->base_link never resolved: {last_err}'

    # --- Layer 4: Navigation -------------------------------------------
    def send_goal_and_watch(self, x, y):
        if not self._nav_client.wait_for_server(timeout_sec=10.0):
            return False, 'navigate_to_pose action server unavailable'

        goal = NavigateToPose.Goal()
        goal.pose.header.frame_id = 'map'
        goal.pose.pose.position.x = x
        goal.pose.pose.position.y = y
        goal.pose.pose.orientation.w = 1.0

        send_future = self._nav_client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, send_future, timeout_sec=10.0)
        handle = send_future.result()
        if handle is None or not handle.accepted:
            return False, 'goal rejected or send timed out'
        goal_id = handle.goal_id.uuid

        # 120s, not 60s: a single internal recovery cycle (progress-checker
        # abort -> BT retry -> succeed) has been observed live to take
        # ~40-50s end to end under this CPU-constrained environment. A
        # shorter window reports a false FAIL on a goal that's still
        # genuinely in-progress, not stalled -- verified by cross-checking
        # the action's GoalStatusArray again after such a "timeout" and
        # finding STATUS_SUCCEEDED already recorded.
        deadline = time.time() + 120.0
        while time.time() < deadline:
            rclpy.spin_once(self, timeout_sec=0.3)
            for entry in self._status_list:
                if bytes(entry.goal_info.goal_id.uuid) != bytes(goal_id):
                    continue
                status = entry.status
                name = STATUS_NAMES.get(status, str(status))
                if status == GoalStatus.STATUS_SUCCEEDED:
                    return True, f'goal SUCCEEDED'
                if status in (GoalStatus.STATUS_ABORTED, GoalStatus.STATUS_CANCELED):
                    return False, f'goal terminated as {name} (not a measurement gap -- the real terminal status)'
        return False, 'no terminal status observed within 120s'


def _transient_local_qos(depth=1):
    return QoSProfile(
        depth=depth,
        reliability=QoSReliabilityPolicy.RELIABLE,
        durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--goal-x', type=float, default=0.6)
    parser.add_argument('--goal-y', type=float, default=0.0)
    args = parser.parse_args()

    rclpy.init()
    node = VerifyScenarioB()
    results = []

    ok, detail = node.check_slam_layer()
    results.append(('Layer 1: SLAM (/map)', ok, detail))

    ok, detail = node.check_nav2_lifecycle()
    results.append(('Layer 2: Nav2 lifecycle', ok, detail))

    ok, detail = node.check_tf_layer()
    results.append(('Layer 3: TF (map->base_link)', ok, detail))

    ok, detail = node.send_goal_and_watch(args.goal_x, args.goal_y)
    results.append(('Layer 4: Navigation goal', ok, detail))

    print('\n=== Scenario B verification report ===')
    for name, ok, detail in results:
        print(f'[{"PASS" if ok else "FAIL"}] {name}: {detail}')
    overall = all(r[1] for r in results)
    print(f'\nOVERALL: {"PASS" if overall else "FAIL"}')
    print('A FAIL on Layer 4 with a clean ABORTED/CANCELED status means Nav2')
    print('correctly detected and reported a navigation failure -- check the')
    print('detail message and controller_server logs before assuming a bug.')

    node.destroy_node()
    rclpy.shutdown()
    sys.exit(0 if overall else 1)


if __name__ == '__main__':
    main()
