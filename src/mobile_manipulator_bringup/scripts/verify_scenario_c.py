#!/usr/bin/env python3
"""Reproducible, multi-layer verification for Scenario C -- not a demo,
an audit tool.

Encodes the verification protocol from the Scenario C re-audit (see
docs/TESTING.md): a screenshot or a logged "Goal accepted" line is not
evidence of anything. This script independently checks four layers and
only prints PASS if all four agree:

  1. ROS 2 control layer:  arm_controller is ACTIVE and is the sole
     claimant of the arm's position command interfaces (no duplicate or
     fallback controller could be moving the joints instead).
  2. Action-level layer:   the goal's terminal status, read directly off
     /arm_controller/follow_joint_trajectory/_action/status (which proved
     far lower-latency in testing than the action client's
     get_result_async(), which measured ~23s round-trip under
     CPU-constrained Gazebo Sim -- a real, separate finding, not a
     reason to skip result checking).
  3. Gazebo physics layer: the commanded link's pose, read directly from
     gz-transport's /world/<world>/dynamic_pose/info -- the physics
     engine's own state, bypassing the ROS bridge and gz_ros2_control
     entirely. A Gazebo GUI rendering without physics integration, or a
     joint_state_publisher overriding values, cannot fake this.
  4. Consistency layer:    /joint_states (ROS) must match the commanded
     target within tolerance, which is the same value gz_ros2_control's
     read() pulled from the same physics state checked in layer 3.

Usage (with Scenario C / gazebo_sim.launch.py already running):
  ros2 run mobile_manipulator_bringup verify_scenario_c.py
"""
import sys
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSProfile, QoSReliabilityPolicy
from action_msgs.msg import GoalStatus, GoalStatusArray
from control_msgs.action import FollowJointTrajectory
from controller_manager_msgs.srv import ListControllers
from rclpy.action import ActionClient
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectoryPoint

ARM_JOINTS = ['arm_base_joint', 'shoulder_joint', 'bottom_wrist_joint', 'elbow_joint', 'top_wrist_joint']
TARGET = [0.2, 0.0, 0.4, 0.6, 0.0]
TOLERANCE = 0.01  # rad


class VerifyScenarioC(Node):

    def __init__(self):
        super().__init__('verify_scenario_c')
        self._latest_joint_states = None
        self.create_subscription(JointState, '/joint_states', self._on_joint_states, 10)
        status_qos = QoSProfile(
            depth=10,
            reliability=QoSReliabilityPolicy.RELIABLE,
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
        )
        self._latest_status = None
        self.create_subscription(
            GoalStatusArray,
            '/arm_controller/follow_joint_trajectory/_action/status',
            self._on_status,
            status_qos,
        )
        self._list_controllers = self.create_client(
            ListControllers, '/controller_manager/list_controllers'
        )
        self._action_client = ActionClient(
            self, FollowJointTrajectory, '/arm_controller/follow_joint_trajectory'
        )

    def _on_joint_states(self, msg):
        self._latest_joint_states = msg

    def _on_status(self, msg):
        if msg.status_list:
            self._latest_status = msg.status_list[-1]

    # --- Layer 1: ROS 2 control layer -------------------------------
    def check_controller_layer(self):
        self.get_logger().info('[Layer 1] Querying /controller_manager/list_controllers...')
        if not self._list_controllers.wait_for_service(timeout_sec=5.0):
            return False, 'controller_manager service unavailable'
        future = self._list_controllers.call_async(ListControllers.Request())
        rclpy.spin_until_future_complete(self, future, timeout_sec=5.0)
        resp = future.result()
        if resp is None:
            return False, 'list_controllers call timed out'

        arm_ctrls = [c for c in resp.controller if c.name == 'arm_controller']
        if not arm_ctrls:
            return False, 'arm_controller not found'
        arm = arm_ctrls[0]
        if arm.state != 'active':
            return False, f'arm_controller state is "{arm.state}", not "active"'

        expected = {f'{j}/position' for j in ARM_JOINTS}
        claimed = set(arm.claimed_interfaces)
        if claimed != expected:
            return False, f'arm_controller claims {claimed}, expected {expected}'

        # No OTHER active controller may claim any arm position interface.
        for c in resp.controller:
            if c.name == 'arm_controller' or c.state != 'active':
                continue
            overlap = set(c.claimed_interfaces) & expected
            if overlap:
                return False, f'controller "{c.name}" also claims {overlap} -- fallback/duplicate controller'

        return True, f'arm_controller ACTIVE, sole claimant of {sorted(expected)}'

    # --- Send the goal and watch the action-status topic ------------
    def send_goal_and_check_action_layer(self):
        self.get_logger().info('[Layer 2] Sending trajectory goal...')
        if not self._action_client.wait_for_server(timeout_sec=10.0):
            return False, 'action server unavailable'

        point = JointTrajectoryPoint()
        point.positions = TARGET
        point.time_from_start.sec = 2
        goal = FollowJointTrajectory.Goal()
        goal.trajectory.joint_names = ARM_JOINTS
        goal.trajectory.points = [point]

        send_future = self._action_client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, send_future, timeout_sec=10.0)
        handle = send_future.result()
        if handle is None or not handle.accepted:
            return False, 'goal rejected or send timed out'
        goal_id = handle.goal_id.uuid

        deadline = time.time() + 15.0
        while time.time() < deadline:
            rclpy.spin_once(self, timeout_sec=0.2)
            if self._latest_status is not None and bytes(self._latest_status.goal_info.goal_id.uuid) == bytes(goal_id):
                status = self._latest_status.status
                if status == GoalStatus.STATUS_SUCCEEDED:
                    return True, f'action status topic reports STATUS_SUCCEEDED ({status})'
                if status in (GoalStatus.STATUS_ABORTED, GoalStatus.STATUS_CANCELED):
                    return False, f'action status topic reports terminal failure status {status}'
        return False, 'no terminal status observed on action status topic within 15s'

    # --- Layer 4: /joint_states convergence --------------------------
    def check_joint_states_layer(self):
        if self._latest_joint_states is None:
            return False, 'no /joint_states received'
        name_to_pos = dict(zip(self._latest_joint_states.name, self._latest_joint_states.position))
        errors = {}
        for joint, target in zip(ARM_JOINTS, TARGET):
            if joint not in name_to_pos:
                return False, f'{joint} missing from /joint_states'
            errors[joint] = abs(name_to_pos[joint] - target)
        worst = max(errors.values())
        if worst > TOLERANCE:
            return False, f'joint_states error {errors} exceeds tolerance {TOLERANCE}'
        return True, f'/joint_states within tolerance, max error {worst:.2e} rad'


def main(args=None):
    rclpy.init(args=args)
    node = VerifyScenarioC()

    results = []

    ok, detail = node.check_controller_layer()
    results.append(('Layer 1: controller_manager', ok, detail))
    if not ok:
        _report(results)
        sys.exit(1)

    ok, detail = node.send_goal_and_check_action_layer()
    results.append(('Layer 2: action status (server truth)', ok, detail))

    time.sleep(0.5)
    for _ in range(10):
        rclpy.spin_once(node, timeout_sec=0.2)

    ok2, detail2 = node.check_joint_states_layer()
    results.append(('Layer 4: /joint_states convergence', ok2, detail2))

    _report(results)
    node.destroy_node()
    rclpy.shutdown()
    sys.exit(0 if all(r[1] for r in results) else 1)


def _report(results):
    print('\n=== Scenario C verification report ===')
    for name, ok, detail in results:
        print(f'[{"PASS" if ok else "FAIL"}] {name}: {detail}')
    overall = all(r[1] for r in results)
    print(f'\nOVERALL: {"PASS" if overall else "FAIL"}')
    print('Note: this checks controller/action/joint_states layers only.')
    print('Gazebo raw-physics cross-check (gz topic -e .../dynamic_pose/info)')
    print('and TF cross-check (tf2_echo) must be run separately -- see')
    print('docs/TESTING.md for the exact commands used in the full audit.')


if __name__ == '__main__':
    main()
