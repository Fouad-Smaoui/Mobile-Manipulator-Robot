# Testing Log

This documents what was *actually run*, where, and what happened —
not what should theoretically work. Updated as real test passes happen;
entries are dated and tied to a commit.

## Environment

Two environments were used:

1. Docker image `ros2-jazzy-ros2-jazzy:latest` (ROS 2 Jazzy, Ubuntu 24.04 Noble), repo bind-mounted as a colcon workspace. Headless (no X server) — `gz sim ... -s` server-only mode throughout. No GPU, running under Docker Desktop on Windows (WSL2 backend) — meaningfully more CPU-constrained than a native Linux host. This matters for the Scenario B result below.
2. WSL Ubuntu 24.04 directly (not Docker), with the repo's `src/` copied into a native-filesystem workspace (`~/mobile_manipulator_ws`) rather than building on `/mnt/c/...` (DrvFS doesn't reliably support the symlinks `colcon build --symlink-install` needs). Windows 11's WSLg gives this instance a real GUI compositor, so `rviz2` and `gz sim`'s GUI render as native windows on the Windows desktop — used to **visually** confirm RViz and Gazebo Sim, not just check logs/topics.

## Visual verification (WSL + WSLg)

With packages installed (`ros-jazzy-gz-ros2-control`, `ros-jazzy-nav2-bringup`, `ros-jazzy-slam-toolbox`, `ros-jazzy-joint-state-publisher-gui`, `ros-jazzy-rviz2`, etc.) and the workspace built fresh in `~/mobile_manipulator_ws`:

- `ros2 launch mobile_manipulator_bringup display.launch.py` — RViz and the joint-slider GUI both appeared as native windows; user confirmed the robot model (base + 5-DOF arm) rendered correctly, no missing meshes.
- `ros2 launch mobile_manipulator_gazebo gazebo_sim.launch.py` — Gazebo Sim's GUI appeared with the robot spawned next to the `pick_table` model; user confirmed visually.
- Drove the robot live: published `TwistStamped{linear.x: 0.3, angular.z: 0.2}` to `/mobile_base_controller/cmd_vel` for ~4s. `/mobile_base_controller/odom` advanced to `x: 0.280, y: 0.023` with yaw rotation — robot visibly moved forward and curved in the Gazebo window.
- Ran `pick_place_demo.py` against the same live sim: goal accepted, `/joint_states` afterward showed `bottom_wrist_joint = 0.300`, `elbow_joint = 1.200` — arm visibly swung toward the table.

### Real bugs found only in this environment (not in Docker)

9. **Stale `ros-jazzy-fastcdr` package** (dated April 2025) installed alongside newer FastRTPS/typesupport packages (Aug–Oct 2025) caused `undefined symbol: _ZN8eprosima7fastcdr3Cdr9serializeERKh` crashes in `controller_manager` spawners and `gz sim` itself. Fixed with `apt-get install --only-upgrade ros-jazzy-fastcdr && apt-get upgrade`. This is an environment-consistency issue, not a repo bug, but it fully blocked Gazebo from starting until fixed — worth checking `dpkg -l | grep -i fastcdr` for matching dates if `gz sim`/`controller_manager` crash with symbol-lookup errors on any machine.
10. **Cross-launch `/robot_description` collision**: running `display.launch.py` (which launches its own `robot_state_publisher` with `sim_mode:=false`) at the same time as `gazebo_sim.launch.py` (`sim_mode:=true`) caused `gz_ros_control`'s embedded `controller_manager` to load the **wrong** hardware plugin (`mobile_manipulator_hardware/MobileManipulatorSystem` instead of `gz_ros2_control/GazeboSimSystem`), because neither launch file namespaces its nodes and both publish to the same global `/robot_description` topic with `transient_local` durability — a late subscriber can pick up either publisher's retained message non-deterministically. Confirmed by inspecting both `robot_state_publisher` processes' actual resolved `--params-file` content directly. **Not a code bug** — each launch file is correct in isolation — but a real gotcha: don't run two of this repo's launch files that both bring up `robot_state_publisher` at the same time without namespacing.

## Why this exists

The repository originally targeted ROS 2 Humble + Gazebo Classic. The
actual available test environments (this Docker image, and a WSL Ubuntu
24.04 instance) are ROS 2 Jazzy, which does not ship Gazebo Classic at
all — only the new Gazebo Sim (Harmonic+) stack via `ros_gz_sim` /
`gz_ros2_control`. The simulation packages were ported to that stack
specifically so they could be tested against a real environment instead
of being verified only by reading config files.

## What was verified by actually running it

### Build
`colcon build --symlink-install` — all 6 packages build clean from a
fresh `rm -rf build install log`.

### Kinematic tree
`check_urdf` on the fully-expanded xacro: single root (`base_link`), no
dual-parent bug, `arm_mount -> arm_base -> bicep -> bottom_wrist -> elbow
-> top_wrist -> tool0` chain intact.

### Scenario A — Teleoperation
Launched `gazebo_sim.launch.py` headless. Confirmed via live topic
inspection:
- `gz_ros2_control` loaded `MobileManipulatorSystem` hardware and
  activated it.
- All three controllers (`arm_controller`, `joint_state_broadcaster`,
  `mobile_base_controller`) loaded and activated with no errors.
- Published a `TwistStamped` to `/mobile_base_controller/cmd_vel` at
  0.3 m/s forward for ~6s. Resulting `/mobile_base_controller/odom`:
  `x: 0.864, y: 0.058`, with a small accumulated yaw — real differential-
  drive motion, not a static value.
- `/tf` publishes `odom -> base_link`.

### Scenario C — Mobile Manipulation
With the same sim running, executed `pick_place_demo.py`. The
`FollowJointTrajectory` goal was accepted by `arm_controller`, and
`/joint_states` afterward showed `bottom_wrist_joint = 0.300`,
`elbow_joint = 1.200` — matching the script's `REACH_POSE` exactly. The
arm moved to the commanded pose in the live simulation.

### Scenario B — Autonomous Navigation
Partially verified. The Nav2 parameter file itself loads correctly (the
rectangular `footprint` polygon and all costmap/controller plugins are
accepted with no parameter exceptions). `controller_server` activated and
established its lifecycle bond. `planner_server`, `behavior_server`, and
`bt_navigator` were commanded to activate but had not confirmed their
lifecycle bonds by the time testing stopped — this container's `gz sim`
process alone was using >200% CPU with no GPU, and the stall pattern
(sequential activation hanging mid-bond-handshake) is consistent with
lifecycle bond-watchdog timeouts under CPU starvation, not a parameter or
config error. **Not yet confirmed**: a full `map -> odom -> base_link`
TF chain and an actual planned path. Re-test on a less constrained host
(native WSL with more cores, or a non-headless run) before claiming this
scenario fully works.

## Real bugs found and fixed by this testing pass (not found by static review)

1. `nav2_params.yaml`'s `robot_radius: 0.35` (circular footprint) was
   wrong for this robot's rectangular chassis — found by measuring the
   actual STL meshes, not by running anything, but confirmed not to
   break Nav2's parameter loading after the fix.
2. `controllers.yaml`'s `wheel_radius: 0.0625` was off by ~60% versus the
   measured mesh (~0.0997m) — same static-measurement origin.
3. The Gazebo integration as first written targeted Gazebo Classic
   (`gazebo_ros2_control`), which doesn't exist on ROS 2 Jazzy at all —
   found by checking the actual installed packages before writing any
   code.
4. `gz_ros2_control`'s exact plugin filename/class names
   (`gz_ros2_control-system` / `gz_ros2_control::GazeboSimROS2ControlPlugin`
   / `gz_ros2_control/GazeboSimSystem`) were verified by inspecting the
   installed `.so` and its `pluginlib` XML description, not assumed from
   memory.
5. `controllers.yaml`'s `joint_state_broadcaster: extra_joints: []` and an
   equivalent empty-list `nav2_params.yaml` `collision_monitor` config
   both crashed with `InvalidParameterValueException` / "parameter not
   initialized" on this rclcpp version — an empty YAML list is
   type-ambiguous to the ROS 2 parameter loader. Fixed by omitting the
   parameter entirely rather than declaring it empty.
6. Gazebo Sim could not resolve `model://mobile_manipulator_description/
   meshes/*.stl` URIs (logged `Unable to find file with URI`) until
   `GZ_SIM_RESOURCE_PATH` was explicitly extended with the package's
   install share directory in `gazebo_sim.launch.py`.
7. `/mobile_base_controller/cmd_vel` is `geometry_msgs/msg/TwistStamped`
   unconditionally on this `diff_drive_controller` build (4.45.2) —
   `use_stamped_vel`/`cmd_vel_unstamped` no longer exist. The teleop
   scenario was assuming the old Humble-era unstamped topic and would
   have silently done nothing (`teleop_twist_keyboard` publishing
   `Twist` to a `TwistStamped` subscriber).
8. `nav2_bringup`'s `navigation_launch.py` (Jazzy) unconditionally brings
   up `collision_monitor` and `docking_server` lifecycle nodes with no
   disable flag; `collision_monitor` requires `observation_sources`,
   which this robot can't provide (no LiDAR yet). Replaced with a local
   `navigation.launch.py` that only launches the four nodes this project
   actually uses.

## Known-not-yet-tested

- Scenario B's full Nav2 + slam_toolbox path with an actual `2D Nav Goal`
  sent and a path executed.
- Real hardware deployment path (`mobile_manipulator_hardware`) — still
  stub-only by design, see `HARDWARE.md`.
