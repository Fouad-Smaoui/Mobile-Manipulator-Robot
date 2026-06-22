"""Spawn the mobile manipulator in Gazebo Classic with ros2_control active.

Brings up, in order: gzserver+gzclient, robot_state_publisher (publishing
/robot_description and TF), entity spawn, then the controllers defined in
mobile_manipulator_control/config/controllers.yaml. Controller spawning is
delayed via event handlers so it only happens once the entity actually
exists in the simulation -- spawning controllers before the entity exists
was the kind of race condition the original launch file did not guard
against.
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_gazebo = get_package_share_directory('mobile_manipulator_gazebo')
    pkg_description = get_package_share_directory('mobile_manipulator_description')
    pkg_gazebo_ros = get_package_share_directory('gazebo_ros')

    world_arg = DeclareLaunchArgument(
        'world',
        default_value=os.path.join(pkg_gazebo, 'worlds', 'mobile_manipulator_world.world'),
        description='Full path to the Gazebo world file',
    )

    robot_description_content = ParameterValue(
        Command([
            'xacro ', os.path.join(pkg_description, 'urdf', 'mobile_manipulator.urdf.xacro'),
            ' sim_mode:=true',
        ]),
        value_type=str,
    )

    gzserver = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, 'launch', 'gzserver.launch.py')
        ),
        launch_arguments={'world': LaunchConfiguration('world')}.items(),
    )

    gzclient = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, 'launch', 'gzclient.launch.py')
        ),
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description_content}],
    )

    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=['-topic', 'robot_description', '-entity', 'mobile_manipulator'],
        output='screen',
    )

    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster'],
    )

    mobile_base_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['mobile_base_controller'],
    )

    arm_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['arm_controller'],
    )

    # Only spawn controllers once the entity has finished spawning.
    delayed_controllers = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_entity,
            on_exit=[
                joint_state_broadcaster_spawner,
                mobile_base_controller_spawner,
                arm_controller_spawner,
            ],
        )
    )

    return LaunchDescription([
        world_arg,
        gzserver,
        gzclient,
        robot_state_publisher,
        spawn_entity,
        delayed_controllers,
    ])
