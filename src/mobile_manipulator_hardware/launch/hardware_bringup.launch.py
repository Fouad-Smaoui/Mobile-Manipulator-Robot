"""Real-hardware bringup path (sim_mode:=false).

Launches robot_state_publisher + controller_manager against the
`mobile_manipulator_hardware/MobileManipulatorSystem` ros2_control plugin
instead of Gazebo, plus the motor/FPGA bridge nodes. The ros2_control
hardware plugin itself is a documented reference skeleton (see
doc/reference/mobile_manipulator_system.hpp) and is NOT yet implemented as
a loadable pluginlib .so -- running this launch file today will fail at
the controller_manager hardware-plugin-load step. It exists to make the
intended deployment path concrete and reviewable rather than aspirational
prose; see doc/HARDWARE.md for what's required to make it load for real.
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.substitutions import Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_description = get_package_share_directory('mobile_manipulator_description')
    pkg_control = get_package_share_directory('mobile_manipulator_control')
    pkg_hardware = get_package_share_directory('mobile_manipulator_hardware')

    robot_description_content = ParameterValue(
        Command([
            'xacro ', os.path.join(pkg_description, 'urdf', 'mobile_manipulator.urdf.xacro'),
            ' sim_mode:=false',
        ]),
        value_type=str,
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description_content}],
    )

    controller_manager = Node(
        package='controller_manager',
        executable='ros2_control_node',
        parameters=[
            {'robot_description': robot_description_content},
            os.path.join(pkg_control, 'config', 'controllers.yaml'),
        ],
        output='screen',
    )

    motor_driver_bridge = Node(
        package='mobile_manipulator_hardware',
        executable='motor_driver_bridge',
        parameters=[os.path.join(pkg_hardware, 'config', 'hardware_config.yaml')],
        output='screen',
    )

    fpga_bridge = Node(
        package='mobile_manipulator_hardware',
        executable='fpga_bridge',
        parameters=[os.path.join(pkg_hardware, 'config', 'hardware_config.yaml')],
        output='screen',
    )

    return LaunchDescription([
        robot_state_publisher,
        controller_manager,
        motor_driver_bridge,
        fpga_bridge,
    ])
