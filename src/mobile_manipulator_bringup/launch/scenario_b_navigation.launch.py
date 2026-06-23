"""Scenario B -- Autonomous Navigation.

Gazebo sim + slam_toolbox (online mapping, since no pre-built map exists
yet -- see doc/SCENARIOS.md roadmap note) + our own trimmed Nav2 launch
(navigation.launch.py) against config/nav2_params.yaml. Demonstrates: TF
tree correctness (map -> odom -> base_link required by costmaps),
velocity command path through mobile_base_controller, and a Nav2 stack
actually able to plan on this robot's footprint.

Uses navigation.launch.py instead of nav2_bringup's navigation_launch.py
directly: verified against an actual run that the latter unconditionally
brings up collision_monitor/docking_server with no disable flag, and
lifecycle_manager aborts the whole bringup if collision_monitor can't get
an observation_sources sensor we don't have. See navigation.launch.py's
docstring for the full story.
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
            os.path.join(pkg_bringup, 'launch', 'navigation.launch.py')
        ),
        launch_arguments={
            'params_file': LaunchConfiguration('params_file'),
        }.items(),
    )

    return LaunchDescription([params_arg, sim, slam, nav2])
