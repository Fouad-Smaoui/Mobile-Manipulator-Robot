"""Spawn ros2_control controllers against an already-running controller_manager.

Used standalone when controller_manager is brought up elsewhere (e.g. by a
real hardware bringup launch file) and you only need to (re)spawn the
controller set defined in config/controllers.yaml.
"""
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='controller_manager',
            executable='spawner',
            arguments=['joint_state_broadcaster'],
            output='screen',
        ),
        Node(
            package='controller_manager',
            executable='spawner',
            arguments=['mobile_base_controller'],
            output='screen',
        ),
        Node(
            package='controller_manager',
            executable='spawner',
            arguments=['arm_controller'],
            output='screen',
        ),
    ])
