"""Spawn the mobile manipulator in Gazebo Sim (Harmonic+) with ros2_control active.

Targets ROS2 Jazzy + ros_gz_sim/gz_ros2_control -- the stack actually
available on this project's test environments (WSL Ubuntu 24.04 and a
Jazzy Docker image both ship Gazebo Sim, not Gazebo Classic; verified by
checking installed packages directly rather than assuming).

Brings up, in order: gz sim (server+GUI together), robot_state_publisher
(publishing /robot_description and TF), a /clock bridge (so ROS nodes
using use_sim_time stay in step with simulated time), entity spawn via
ros_gz_sim's `create`, then the controllers defined in
mobile_manipulator_control/config/controllers.yaml. Controller spawning
is delayed via an event handler so it only happens once the entity
actually exists in the simulation.
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    AppendEnvironmentVariable,
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    RegisterEventHandler,
)
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration, PythonExpression
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_gazebo = get_package_share_directory('mobile_manipulator_gazebo')
    pkg_description = get_package_share_directory('mobile_manipulator_description')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')

    # Without this, gz-sim can't resolve the `model://mobile_manipulator_description/...`
    # mesh URIs produced by the URDF->SDF conversion of our `package://...`
    # mesh paths -- confirmed by an actual headless run logging
    # "Unable to find file with URI [model://mobile_manipulator_description/...]"
    # until this was added. /opt/ros/jazzy/share is on GZ_SIM_RESOURCE_PATH
    # by default; this adds the equivalent parent share dir for our own
    # install prefix.
    set_gz_resource_path = AppendEnvironmentVariable(
        'GZ_SIM_RESOURCE_PATH',
        os.path.dirname(pkg_description),
    )

    world_arg = DeclareLaunchArgument(
        'world',
        default_value=os.path.join(pkg_gazebo, 'worlds', 'mobile_manipulator_world.world'),
        description='Full path to the Gazebo Sim world file',
    )

    headless_arg = DeclareLaunchArgument(
        'headless',
        default_value='false',
        description="Run gz sim server-only (no GUI window) via '-s'",
    )

    robot_description_content = ParameterValue(
        Command([
            'xacro ', os.path.join(pkg_description, 'urdf', 'mobile_manipulator.urdf.xacro'),
            ' sim_mode:=true',
        ]),
        value_type=str,
    )

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={
            'gz_args': [
                '-r ',
                LaunchConfiguration('world'),
                PythonExpression([
                    "' -s' if '", LaunchConfiguration('headless'), "' == 'true' else ''",
                ]),
            ],
        }.items(),
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description_content, 'use_sim_time': True}],
    )

    # Gazebo Sim runs its own simulated clock; bridge it to ROS so any
    # node with use_sim_time:=true (robot_state_publisher, nav2,
    # slam_toolbox) stays synchronized with it instead of the wall clock.
    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
        output='screen',
    )

    spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-topic', 'robot_description', '-name', 'mobile_manipulator'],
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
        set_gz_resource_path,
        world_arg,
        headless_arg,
        gz_sim,
        clock_bridge,
        robot_state_publisher,
        spawn_entity,
        delayed_controllers,
    ])
