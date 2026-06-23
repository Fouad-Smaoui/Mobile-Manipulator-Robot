# Demonstration Scenarios

All three scenarios assume `colcon build && source install/setup.bash` has
been run from the workspace root, and ROS 2 Jazzy + Gazebo Sim (Harmonic+)
are installed (`ros-jazzy-ros-gz-sim`, `ros-jazzy-gz-ros2-control`).

Scenarios A and C below have been run end-to-end in a headless ROS 2
Jazzy Docker container with real evidence (odometry actually advancing,
joint states actually matching the commanded goal) — see
[`docs/TESTING.md`](../../../docs/TESTING.md) for the exact log output.
Scenario B's Nav2 stack loads and partially activates but full
end-to-end navigation has not yet been confirmed; see that doc for
specifics before relying on it.

## Scenario A — Teleoperation

```bash
ros2 launch mobile_manipulator_bringup scenario_a_teleop.launch.py
```

**What it demonstrates:** working URDF, `gz_ros2_control` bridge,
`diff_drive_controller` velocity interface end-to-end.

**Expected output:**
- Gazebo opens with the robot spawned on the ground plane next to the
  `pick_table` model.
- An `xterm` opens running `teleop_twist_keyboard` (with `stamped:=true`
  so it matches `/mobile_base_controller/cmd_vel`'s `TwistStamped` type —
  verified live that this controller no longer accepts a plain
  `Twist`/`cmd_vel_unstamped`, unlike Humble-era `diff_drive_controller`);
  arrow keys drive the base.
- `ros2 topic hz /mobile_base_controller/odom` shows odometry publishing.
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

Uses this package's own `navigation.launch.py` (4 lifecycle nodes:
`controller_server`, `planner_server`, `behavior_server`, `bt_navigator`)
rather than `nav2_bringup`'s `navigation_launch.py` directly — verified
live that the latter unconditionally brings up `collision_monitor` and
`docking_server` with no disable flag, and `lifecycle_manager` aborts the
*entire* bringup when `collision_monitor` can't get an
`observation_sources` sensor this robot doesn't have yet.

**Expected output:**
- Gazebo + `slam_toolbox` + the trimmed Nav2 launch come up.
- `ros2 topic list` shows `/map`, `/plan`, `/mobile_base_controller/cmd_vel`.
- Sending a `2D Nav Goal` from RViz (add `rviz2` separately) drives the
  base toward the goal.

**Verification status:** partial — see [`docs/TESTING.md`](../../../docs/TESTING.md).
The parameter file loads cleanly and `controller_server` activates and
bonds; `planner_server`/`behavior_server`/`bt_navigator` were still
completing their lifecycle bond handshake when testing stopped in a
CPU-constrained headless container. Re-verify on a less constrained host
before relying on this scenario as proof of working navigation.

**Known limitation (honest, not hidden):** there is no LiDAR on the robot
yet (confirmed absent in the forensic audit), so `local_costmap`/
`global_costmap` are configured to consume `/scan` but nothing publishes
it until a LiDAR is added to `base.xacro` and `mobile_manipulator.gazebo.xacro`
(see the commented sensor block already in that file). Until then this
scenario demonstrates the *navigation stack wiring*, not obstacle-aware
navigation.

**Verified against geometry, not assumed:** `config/nav2_params.yaml`
defines `footprint` as a rectangular polygon derived from the actual STL
bounding boxes (`robot_base.stl`, `wheel.stl`), not a circular
`robot_radius` — the simplification standard in turtlebot/kobuki-style
nav2 demos, which doesn't fit this robot's rectangular 4-wheel chassis.
`mobile_manipulator_control/config/controllers.yaml`'s `wheel_radius` was
likewise corrected from an unverified 0.0625m (carried over from the
original repo) to ~0.0997m, measured from `wheel.stl`.

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

**Verified, with a screenshot, not just logs:** run live via WSL+WSLg —
goal accepted by `arm_controller`, `/joint_states` confirmed
`bottom_wrist_joint = 0.300` and `elbow_joint = 1.200` (exactly matching
`REACH_POSE`) while the simulation was running, and a screenshot was
captured directly from Gazebo's own render buffer (the `/gui/screenshot`
service — plain X11 window-grab tools like `scrot` capture solid black
for GPU-rendered windows under WSLg, a real gotcha logged in
`docs/TESTING.md`):

![Scenario C: arm reaching toward the pick table in Gazebo](../../../images/scenario_c_manipulation_gazebo.png)

**Known limitation (honest, not hidden):** this is a scripted joint-space
goal, not an IK-driven pick-and-place — there is no MoveIt config and no
grasp planning yet. See the top-level README roadmap for the MoveIt +
gripper upgrade path that turns this into a real pick-and-place demo.
