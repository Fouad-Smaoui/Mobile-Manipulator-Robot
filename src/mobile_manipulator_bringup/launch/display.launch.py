"""RViz-only visualization, no Gazebo, no ros2_control.

Fastest path to actually see the robot: robot_state_publisher +
joint_state_publisher_gui (sliders for every joint) + RViz. This is the
"30-second sanity check" launch -- use gazebo_sim.launch.py for anything
that needs physics or controllers.
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.substitutions import Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_description = get_package_share_directory('mobile_manipulator_description')

    robot_description_content = ParameterValue(
        Command([
            'xacro ', os.path.join(pkg_description, 'urdf', 'mobile_manipulator.urdf.xacro'),
            ' sim_mode:=false',
        ]),
        value_type=str,
    )

    return LaunchDescription([
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': robot_description_content}],
        ),
        Node(
            package='joint_state_publisher_gui',
            executable='joint_state_publisher_gui',
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', os.path.join(pkg_description, 'rviz', 'mobile_manipulator.rviz')],
        ),
    ])
