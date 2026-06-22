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


def main(args=None):
    rclpy.init(args=args)
    node = PickPlaceDemo()
    node.send_reach_goal()
    rclpy.spin(node)


if __name__ == '__main__':
    main()
