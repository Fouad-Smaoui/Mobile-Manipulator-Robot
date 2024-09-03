import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'robot_description_file',
            default_value=os.path.join(
                get_package_share_directory('robot_description'),
                'urdf', 'robot_base.urdf.xacro'
            ),
            description='Path to the robot description xacro file'
        ),
        DeclareLaunchArgument(
            'control_config_file',
            default_value=os.path.join(
                get_package_share_directory('robot_description'),
                'config', 'control.yaml'
            ),
            description='Path to the control configuration file'
        ),
        Node(
            package='gazebo_ros',
            executable='/usr/bin/gzserver',
            name='gzserver',
            output='screen',
            arguments=['-s', 'libgazebo_ros_factory.so']
        ),
        Node(
            package='gazebo_ros',
            executable='/usr/bin/gzclient',
            name='gzclient',
            output='screen'
        ),
        Node(
            package='gazebo_ros',
            executable='spawn_entity.py',
            name='spawn_urdf',
            arguments=[
                '-file', LaunchConfiguration('robot_description_file'),
                '-entity', 'robot_base'
            ],
            output='screen'
        ),
        Node(
            package='controller_manager',
            executable='spawner',
            name='base_controller_spawner',
            arguments=[
                'robot_base_joint_publisher',
                'robot_base_velocity_controller'
            ],
            output='screen'
        ),
    ])
