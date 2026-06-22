"""Scenario A -- Teleoperation.

Brings up the full Gazebo simulation (description + ros2_control +
controllers) and opens a teleop_twist_keyboard terminal publishing
/cmd_vel to mobile_base_controller. Demonstrates: working URDF, working
ros2_control velocity interface, working diff-drive kinematics.

See doc/SCENARIOS.md for expected terminal output and how to verify
/odom and TF are publishing.
"""
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    pkg_gazebo = get_package_share_directory('mobile_manipulator_gazebo')

    sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo, 'launch', 'gazebo_sim.launch.py')
        )
    )

    teleop = Node(
        package='teleop_twist_keyboard',
        executable='teleop_twist_keyboard',
        prefix='xterm -e',
        output='screen',
        remappings=[('/cmd_vel', '/mobile_base_controller/cmd_vel_unstamped')],
    )

    return LaunchDescription([sim, teleop])
