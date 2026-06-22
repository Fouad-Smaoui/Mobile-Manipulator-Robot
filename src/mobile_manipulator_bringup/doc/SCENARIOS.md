# Demonstration Scenarios

All three scenarios assume `colcon build && source install/setup.bash` has
been run from the workspace root, and ROS 2 Humble + Gazebo Classic 11 are
installed.

## Scenario A — Teleoperation

```bash
ros2 launch mobile_manipulator_bringup scenario_a_teleop.launch.py
```

**What it demonstrates:** working URDF, `gazebo_ros2_control` bridge,
`diff_drive_controller` velocity interface end-to-end.

**Expected output:**
- Gazebo opens with the robot spawned on the ground plane next to the
  `pick_table` model.
- An `xterm` opens running `teleop_twist_keyboard`; arrow keys drive the
  base.
- `ros2 topic hz /mobile_base_controller/odom` shows ~50 Hz odometry.
- `ros2 run tf2_tools view_frames` shows an unbroken `odom -> base_link`
  chain (and `base_link -> base_footprint`, `base_link -> arm_mount -> …`).

## Scenario B — Autonomous Navigation

```bash
ros2 launch mobile_manipulator_bringup scenario_b_navigation.launch.py
```

**What it demonstrates:** Nav2 stack able to load this robot's footprint
and costmap config, `slam_toolbox` building a map online (no static map
is checked in — see roadmap below), TF tree satisfying Nav2's `map ->
odom -> base_link` requirement.

**Expected output:**
- Gazebo + `slam_toolbox` + `nav2_bringup`'s `navigation_launch.py` come up.
- `ros2 topic list` shows `/map`, `/plan`, `/cmd_vel`.
- Sending a `2D Nav Goal` from RViz (add `rviz2` separately, or use
  `nav2_bringup`'s own RViz config) drives the base toward the goal.

**Known limitation (honest, not hidden):** there is no LiDAR on the robot
yet (confirmed absent in the forensic audit), so `local_costmap`/
`global_costmap` are configured to consume `/scan` but nothing publishes
it until a LiDAR is added to `base.xacro` and `mobile_manipulator.gazebo.xacro`
(see the commented sensor block already in that file). Until then this
scenario demonstrates the *navigation stack wiring*, not obstacle-aware
navigation.

## Scenario C — Mobile Manipulation

```bash
ros2 launch mobile_manipulator_bringup scenario_c_manipulation.launch.py
```

**What it demonstrates:** a `FollowJointTrajectory` goal flowing from a
ROS 2 action client through `joint_trajectory_controller` into simulated
arm motion in Gazebo.

**Expected output:**
- Gazebo opens with the robot next to the pick table.
- After ~8s (giving controllers time to spawn), the arm swings toward the
  table using the hand-picked joint targets in `scripts/pick_place_demo.py`.

**Known limitation (honest, not hidden):** this is a scripted joint-space
goal, not an IK-driven pick-and-place — there is no MoveIt config and no
grasp planning yet. See the top-level README roadmap for the MoveIt +
gripper upgrade path that turns this into a real pick-and-place demo.
