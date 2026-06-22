"""Scenario C -- Mobile Manipulation.

Gazebo sim + a scripted pick-approach trajectory sent to arm_controller's
FollowJointTrajectory action server. This is intentionally NOT a MoveIt
pick-and-place pipeline (no IK solver exists yet -- see top-level README
roadmap); it demonstrates the piece that does exist end-to-end: a
trajectory goal flowing through ros2_control into simulated arm motion
toward the `pick_table` model placed in the world file.
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    pkg_gazebo = get_package_share_directory('mobile_manipulator_gazebo')

    sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo, 'launch', 'gazebo_sim.launch.py')
        )
    )

    # Give Gazebo + controller spawners time to come up before sending a
    # trajectory goal to a controller that doesn't exist yet.
    pick_place_demo = TimerAction(
        period=8.0,
        actions=[
            Node(
                package='mobile_manipulator_bringup',
                executable='pick_place_demo.py',
                output='screen',
            )
        ],
    )

    return LaunchDescription([sim, pick_place_demo])
