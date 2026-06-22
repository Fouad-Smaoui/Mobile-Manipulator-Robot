"""Scenario B -- Autonomous Navigation.

Gazebo sim + slam_toolbox (online mapping, since no pre-built map exists
yet -- see doc/SCENARIOS.md roadmap note) + Nav2 bringup against
config/nav2_params.yaml. Demonstrates: TF tree correctness (map -> odom ->
base_link required by costmaps), velocity command path through
mobile_base_controller, and a Nav2 stack actually able to plan on this
robot's footprint.
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument


def generate_launch_description():
    pkg_bringup = get_package_share_directory('mobile_manipulator_bringup')
    pkg_gazebo = get_package_share_directory('mobile_manipulator_gazebo')
    pkg_nav2 = get_package_share_directory('nav2_bringup')
    pkg_slam_toolbox = get_package_share_directory('slam_toolbox')

    params_arg = DeclareLaunchArgument(
        'params_file',
        default_value=os.path.join(pkg_bringup, 'config', 'nav2_params.yaml'),
    )

    sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo, 'launch', 'gazebo_sim.launch.py')
        )
    )

    slam = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_slam_toolbox, 'launch', 'online_async_launch.py')
        )
    )

    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_nav2, 'launch', 'navigation_launch.py')
        ),
        launch_arguments={
            'params_file': LaunchConfiguration('params_file'),
            'use_sim_time': 'true',
        }.items(),
    )

    return LaunchDescription([params_arg, sim, slam, nav2])
