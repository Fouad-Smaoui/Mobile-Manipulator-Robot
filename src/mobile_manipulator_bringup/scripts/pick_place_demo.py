#!/usr/bin/env python3
"""Scenario C demo node: sends one scripted "reach toward the table" goal
to arm_controller via the standard JointTrajectoryController action
interface.

This is explicitly a stand-in for MoveIt, not a replacement for it: there
is no IK here, the joint targets below are hand-picked to swing the arm
toward +X (where worlds/mobile_manipulator_world.world places the pick
table). See the top-level README roadmap for the planned MoveIt upgrade.
"""
import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from control_msgs.action import FollowJointTrajectory
from trajectory_msgs.msg import JointTrajectoryPoint

ARM_JOINTS = [
    'arm_base_joint',
    'shoulder_joint',
    'bottom_wrist_joint',
    'elbow_joint',
    'top_wrist_joint',
]

# Hand-picked joint targets (radians) that swing the arm toward the
# pick_table model placed at (1.2, 0, 0.25) in the world file.
REACH_POSE = [0.0, 0.6, 0.3, 1.2, 0.0]


class PickPlaceDemo(Node):

    def __init__(self):
        super().__init__('pick_place_demo')
        self._client = ActionClient(
            self, FollowJointTrajectory, '/arm_controller/follow_joint_trajectory'
        )

    def send_reach_goal(self):
        self.get_logger().info('Waiting for arm_controller action server...')
        self._client.wait_for_server()

        point = JointTrajectoryPoint()
        point.positions = REACH_POSE
        point.time_from_start.sec = 3

        goal = FollowJointTrajectory.Goal()
        goal.trajectory.joint_names = ARM_JOINTS
        goal.trajectory.points = [point]

        self.get_logger().info('Sending reach-toward-table trajectory goal')
        future = self._client.send_goal_async(goal)
        future.add_done_callback(self._on_goal_response)

    def _on_goal_response(self, future):
        handle = future.result()
        if not handle.accepted:
            self.get_logger().error('Goal rejected by arm_controller')
            return
        self.get_logger().info('Goal accepted, arm should now be moving in Gazebo')
        # AUDIT FIX: this used to stop here. Acceptance only means the
        # controller queued the trajectory -- it says nothing about
        # whether the motion actually completed. A real verification
        # pass (see docs/TESTING.md) found this script reported "success"
        # purely on acceptance while never checking the action's terminal
        # result, which is exactly the kind of gap that can hide a
        # trajectory that was accepted but aborted partway through.
        self._get_result_future = handle.get_result_async()
        self._get_result_future.add_done_callback(self._on_result)

    def _on_result(self, future):
        result = future.result()
        status = result.status
        error_code = result.result.error_code
        if status == 4 and error_code == 0:  # GoalStatus.STATUS_SUCCEEDED
            self.get_logger().info(
                f'Trajectory SUCCEEDED (status={status}, error_code={error_code}) '
                '-- arm reached the commanded pose.'
            )
        else:
            self.get_logger().error(
                f'Trajectory did NOT succeed: status={status}, '
                f'error_code={error_code}, error_string="{result.result.error_string}". '
                'Acceptance is not success -- see docs/TESTING.md.'
            )


def main(args=None):
    rclpy.init(args=args)
    node = PickPlaceDemo()
    node.send_reach_goal()
    rclpy.spin(node)


if __name__ == '__main__':
    main()
