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

    # Verified against an actual headless run: this Jazzy diff_drive_controller
    # build (4.45.2) has dropped `use_stamped_vel`/`cmd_vel_unstamped` --
    # `ros2 param get /mobile_base_controller use_stamped_vel` reports
    # "Parameter not set", and `/mobile_base_controller/cmd_vel` is
    # geometry_msgs/msg/TwistStamped unconditionally. teleop_twist_keyboard
    # supports stamped output via its own `stamped`/`frame_id` parameters.
    teleop = Node(
        package='teleop_twist_keyboard',
        executable='teleop_twist_keyboard',
        prefix='xterm -e',
        output='screen',
        parameters=[{'stamped': True, 'frame_id': 'base_link'}],
        remappings=[('/cmd_vel', '/mobile_base_controller/cmd_vel')],
    )

    return LaunchDescription([sim, teleop])
