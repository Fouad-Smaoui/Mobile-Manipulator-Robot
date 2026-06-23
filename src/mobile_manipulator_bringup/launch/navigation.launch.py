"""Minimal Nav2 lifecycle stack: controller_server, planner_server,
behavior_server, bt_navigator -- the four nodes actually needed to take a
goal pose and produce velocity commands.

Verified against an actual run that nav2_bringup's own
`navigation_launch.py` (Jazzy) unconditionally launches 10 lifecycle
nodes including `collision_monitor` and `docking_server`, with no flag to
disable either, and `lifecycle_manager` aborts the *entire* bringup if
any one of them fails to activate. `collision_monitor` requires
`observation_sources` to be a populated parameter -- there is no LiDAR on
this robot yet (see SCENARIOS.md), and an empty-list placeholder hits the
same rclcpp parameter-typing exception `extra_joints: []` did in
controllers.yaml. Rather than configure a safety-monitor node against a
sensor that doesn't exist, this launches only the nodes this project
actually uses.
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_bringup = get_package_share_directory('mobile_manipulator_bringup')

    params_arg = DeclareLaunchArgument(
        'params_file',
        default_value=os.path.join(pkg_bringup, 'config', 'nav2_params.yaml'),
    )
    params_file = LaunchConfiguration('params_file')

    lifecycle_nodes = ['controller_server', 'planner_server', 'behavior_server', 'bt_navigator']

    # controller_server/behavior_server publish velocity commands directly
    # to our diff_drive_controller's real topic -- no cmd_vel_smoothed/
    # collision_monitor hop, since those nodes aren't launched here.
    cmd_vel_remap = [('cmd_vel', '/mobile_base_controller/cmd_vel')]

    controller_server = Node(
        package='nav2_controller',
        executable='controller_server',
        output='screen',
        parameters=[params_file],
        remappings=cmd_vel_remap,
    )

    planner_server = Node(
        package='nav2_planner',
        executable='planner_server',
        output='screen',
        parameters=[params_file],
    )

    behavior_server = Node(
        package='nav2_behaviors',
        executable='behavior_server',
        output='screen',
        parameters=[params_file],
        remappings=cmd_vel_remap,
    )

    # RELIABILITY FIX: stock Nav2 default BT XML's recovery RoundRobin
    # includes a fixed 5s Wait action meant for transient dynamic
    # obstacles (e.g. a person crossing the path) -- this scenario's
    # world is static, so that Wait buys nothing and was measured to
    # burn real wall-clock time across retries on hard-to-plan goals
    # (sharp diagonal/backward paths) without ever actually erroring.
    # Our copy is identical to the stock XML except Wait is cut to 1.0s.
    bt_xml_path = os.path.join(
        pkg_bringup, 'config', 'navigate_to_pose_w_replanning_and_recovery.xml'
    )
    bt_navigator = Node(
        package='nav2_bt_navigator',
        executable='bt_navigator',
        output='screen',
        parameters=[params_file, {'default_nav_to_pose_bt_xml': bt_xml_path}],
    )

    lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_navigation',
        output='screen',
        parameters=[{
            'use_sim_time': True,
            'autostart': True,
            'node_names': lifecycle_nodes,
        }],
    )

    return LaunchDescription([
        params_arg,
        controller_server,
        planner_server,
        behavior_server,
        bt_navigator,
        lifecycle_manager,
    ])
