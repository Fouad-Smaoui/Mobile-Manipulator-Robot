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

**A screenshot is not evidence.** An earlier pass in this log treated a
Gazebo GUI screenshot as proof Scenario C worked. It wasn't — it was a
single visual snapshot with no controller, action, or physics-layer
verification behind it. The repository's own audit principle ("if it
wasn't measured in ROS/Gazebo state, it didn't happen") applies to this
log just as much as to the robot, so that screenshot has been
downgraded to illustrative-only and Scenario C was re-audited from
scratch with independent evidence streams. Full methodology below;
short version: **the original claim holds, for reasons the screenshot
never established, and the re-audit found two real, separate defects
along the way.**

#### Re-audit protocol (2026-06-23, WSL + WSLg, isolated relaunch)

Reproduced cleanly: killed every leftover ROS2/Gazebo process, restarted
the `ros2` daemon, confirmed `ros2 node list` was empty, then launched
`scenario_c_manipulation.launch.py` alone (no `display.launch.py` or
Nav2 running concurrently — see bug #10 above for why that matters).
A `ros2 bag record` of `/joint_states`, `/dynamic_joint_states`, `/tf`,
`/tf_static`, `/arm_controller/controller_state`,
`/arm_controller/transition_event`, `/arm_controller/joint_trajectory`,
`/clock`, `/robot_description` ran throughout (538s, 65,295 messages,
4,767 `/joint_states` and `/arm_controller/controller_state` samples,
3,336 `/tf` transforms — reproducible, inspectable via `ros2 bag info`).

**Layer 1 — ROS 2 control truth** (`/controller_manager/list_controllers`,
queried directly via the service, not inferred from logs):
all three controllers `active`; `arm_controller` claims exactly
`{arm_base_joint, shoulder_joint, bottom_wrist_joint, elbow_joint,
top_wrist_joint}/position` and nothing else claims any of those
interfaces. No duplicate `controller_manager`/`arm_controller` nodes
(`ros2 node list` showed exactly one of each). No `joint_state_publisher`
node was running (ruling out the "GUI slider lying about joint values"
failure mode explicitly).

**Layer 2 — Action-level truth, not just acceptance.** Sent several
goals via `ros2 action send_goal`. Found immediately that `pick_place_demo.py`
*only ever checked goal acceptance* — never the terminal result — which
is exactly the "trajectory accepted but not verified" gap the re-audit
was meant to catch. Reading
`/arm_controller/follow_joint_trajectory/_action/status` directly (a
`GoalStatusArray`, requires matching `TRANSIENT_LOCAL` QoS to see
retained values, this is *not* visible via plain `ros2 topic echo
--once` without `--qos-durability transient_local`) showed the real
per-goal terminal states: `STATUS_CANCELED` (5) for goals preempted by a
later one, `STATUS_SUCCEEDED` (4) for goals that ran to completion —
exactly the behavior a correct preemptible trajectory controller should
have, not a fake uniform "always succeeded."

**Defect found #1 — action result latency.** `ros2 action send_goal`
(and a plain `rclpy` `get_result_async()` client) took **~26 seconds**
to receive the terminal result for a 3-second trajectory, even though
the server-side status topic reported `STATUS_SUCCEEDED` almost
immediately. This is real and reproducible (confirmed 3 times), and is
attributed to DDS/executor scheduling pressure under this
CPU-constrained Gazebo Sim session (the `gz sim` process alone was
measured at 130-400%+ CPU throughout this session) rather than a defect
in the controller itself — the *execution* tracked correctly in real
time per Layer 2's feedback stream (`error.positions` converging toward
zero across consecutive feedback messages, consistent with closed-loop
spline tracking, not an instant teleport). Practical takeaway: don't
synchronously block on `get_result_async()` for time-critical checks in
this kind of environment; poll the status topic instead.

**Layer 3 — Gazebo physics truth, independent of the ROS bridge.**
Queried `/world/mobile_manipulator_world/dynamic_pose/info` via
`gz topic -e` directly — this is the physics engine's (`dartsim`) own
link-pose output, populated by the simulation **server**, not the GUI,
so it cannot be faked by a GUI-only animation. Before/after snapshots of
the `elbow` and `bottom_wrist` link poses for an `arm_base_joint`
(waist-yaw) change from 0 to 0.9 rad showed Z height unchanged to 5
decimal places (correct — that joint doesn't move along Z) while X/Y
shifted measurably (0.191→0.200, 0.029→0.0002) — exactly the geometric
signature of a yaw rotation about the joint's own axis, not an arbitrary
or absent change.

**Layer 4 — Cross-check consistency.** `ros2 run tf2_ros tf2_echo
base_link elbow` reported `[0.200, 0.000, 0.852]`; the raw Gazebo
physics pose for the same link was `[0.20017, 0.00022, 0.85193]` —
agreement to within ~0.2mm. `/joint_states`, TF, and the physics engine
all agree; there is no fake propagation anywhere in the chain.

**Defect found #2 (now fixed) — incomplete verification in
`pick_place_demo.py`.** The script accepted a goal and declared success
in its log line without ever checking the terminal result. Fixed: it
now calls `get_result_async()` and explicitly logs `SUCCEEDED` vs.
failure with the real `error_code`/`error_string`. Verified the fix
itself by re-running it — it correctly printed
`Trajectory SUCCEEDED (status=4, error_code=0)` (after the ~26s latency
described above, which is now a known, documented characteristic, not a
silent gap).

**New reusable audit artifact:** `scripts/verify_scenario_c.py`
(`ros2 run mobile_manipulator_bringup verify_scenario_c.py`) encodes
Layers 1, 2 (via the low-latency status topic, not `get_result_async()`),
and 4 as an automated, repeatable PASS/FAIL check. Run against the live
sim during this audit:
```
[PASS] Layer 1: controller_manager: arm_controller ACTIVE, sole claimant of [...]
[PASS] Layer 2: action status (server truth): action status topic reports STATUS_SUCCEEDED (4)
[PASS] Layer 4: /joint_states convergence: /joint_states within tolerance, max error 5.56e-03 rad
OVERALL: PASS
```
Layer 3 (raw Gazebo physics) and the TF cross-check still require the
manual `gz topic`/`tf2_echo` commands above — not yet automated.

**Causality, stated explicitly:** the arm motion is caused by
`pick_place_demo.py` / `verify_scenario_c.py` sending a
`FollowJointTrajectory` goal → `arm_controller`
(`joint_trajectory_controller`, confirmed sole claimant of the position
interfaces) interpolating a spline and writing position setpoints →
`gz_ros2_control`'s `GazeboSimSystem` hardware interface `write()`
pushing those setpoints into `dartsim` as a proportional position
actuator (`position_proportional_gain = 0.1`, logged at startup) →
physics integrating real torque/motion → `read()` pulling updated joint
state back → `joint_state_broadcaster` publishing `/joint_states` →
`robot_state_publisher` computing `/tf`. Every link in that chain was
independently checked above; none of it is short-circuited.

**Verdict: ✅ Physically correct execution**, established by
controller-state, action-status, raw-physics, and TF evidence agreeing
independently — not by the screenshot, which is now retained only as an
illustration in `SCENARIOS.md`, explicitly labeled as such.

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
9. Items 9-10 are the stale-`fastcdr` and cross-launch `/robot_description`
   collision bugs, numbered in the WSL section above to keep them next
   to the environment they were found in.
10. `pick_place_demo.py` declared success on goal *acceptance* and never
    checked the action's terminal result — found during the Scenario C
    re-audit below. Fixed to check `get_result_async()` and log the real
    `error_code`/`error_string`.
11. Action result delivery (`get_result_async()`/`ros2 action send_goal`)
    took ~26s for a 3s trajectory under this CPU-constrained Gazebo Sim
    session, even though the server-side status topic reported success
    almost immediately. Environment/scheduling characteristic, not a
    controller defect — see Scenario C re-audit below. `verify_scenario_c.py`
    polls the status topic instead of blocking on `get_result_async()`
    to avoid this.

## RViz re-verification (2026-06-23, via the `ros2-skill` Claude Code skill)

Re-ran the `display.launch.py` check using the installed `ros2-skill`
(`~/.claude/skills/ros2-skill/scripts/ros2_cli.py`) instead of raw `ros2`
commands, per the same "don't trust a screenshot" standard applied to
Scenario C. Confirmed independently, not just by looking at the window:

- `ros2_cli.py profile scan` correctly detected this workspace's real
  controllers (`arm_controller`, `joint_state_broadcaster`,
  `mobile_base_controller`) once scoped to `~/mobile_manipulator_ws` —
  the skill ships a bundled example profile (`lekiwi`) that is **not**
  this robot; loading it blindly would have been a real mistake. It also
  initially auto-classified this robot as `humanoid` (false positive
  from `shoulder_joint`/`elbow_joint` name patterns matching its
  humanoid heuristic); corrected with `--robot-type mobile_manipulator`.
- `ros2_cli.py node info /rviz` confirmed RViz's actual ROS graph
  subscriptions: `/robot_description` directly, and `/tf` + `/tf_static`
  via its internal `transform_listener_impl_*` node — i.e. RViz is
  genuinely wired to live state, not a cached/static view.
- Raw `ros2 run tf2_ros tf2_echo base_link tool0` (ground truth,
  independent of any tooling) resolved the full kinematic chain
  end-to-end: `[0.200, 0.000, 1.112]`, 90° yaw — proving every
  intermediate transform in the 5-joint arm chain exists and is correct.

### Three real bugs found in the `ros2-skill` itself

12. **`topics publish` durability/QoS mismatch.** The skill's publisher
    for `/joint_states` used `TRANSIENT_LOCAL` durability;
    `robot_state_publisher`'s subscription is `BEST_EFFORT`/`VOLATILE`.
    Confirmed directly with the skill's own `topics qos-check` command,
    which reported `"compatible": false`. Messages were never received
    by `robot_state_publisher` regardless of publish duration (tested up
    to 25s continuous, both endpoints visible in the ROS graph the whole
    time) — this is a real, reproducible defect in the skill's publish
    path for this case, not a discovery-timing artifact. Worked around
    by writing a 20-line one-off `rclpy` publisher with explicit
    `RELIABLE`/`VOLATILE` QoS instead.
13. **`tf list` / `tf echo` under-report frames.** Even immediately after
    a fresh, known-good launch (confirmed via raw `tf2_echo` in the same
    breath), the skill's `tf list` only ever returned the 3 frames backed
    by `/tf_static` (`arm_mount`, `base_footprint`, `tool0`) and never
    the 9 frames published dynamically via `/tf` — across many retries,
    durations, and timing offsets. Raw `tf2_echo`/`tf2_ros` tooling
    resolved the full tree correctly every time on the same live system.
    Treat this skill's `tf` subcommands as unreliable for completeness
    checks; use raw `tf2_echo` for ground truth.
14. **`run new` / `launch new` source the wrong workspace.** Both
    commands reported `workspace_sourced:
    "/home/fouadroboticist/ros2_ws/install/local_setup.bash"` — an
    unrelated, older workspace from a different project on this machine
    — regardless of which workspace was actually sourced in the calling
    shell before invoking `ros2_cli.py`, and with no documented flag to
    override it. `launch new mobile_manipulator_bringup display.launch.py`
    failed outright with `"Package 'mobile_manipulator_bringup' not
    found"` as a direct consequence. Worked around by launching via plain
    `ros2 launch`/`ros2 run` for this project's own packages, while still
    using the skill for all introspection/diagnosis (profile, node info,
    qos-check, tf ground-truth cross-checks), which worked correctly
    throughout.

### Screenshot technique, generalized beyond Gazebo

Gazebo Sim's own `/gui/screenshot` gz-transport service was the fix for
Scenario C's black-screenshot problem (see above) because it reads the
renderer's framebuffer directly. RViz2 has no equivalent built-in
mechanism, and forcing `LIBGL_ALWAYS_SOFTWARE=1` before launching it did
**not** fix the black-capture problem (`scrot` still produced an
identical-byte-count solid-black PNG).

The actual fix: WSLg renders each Linux GUI app into a **real native
Windows window** (visible in `Get-Process | Where-Object
MainWindowTitle`, hosted under an `msrdc` process) — that's how the
window is visible to a human looking at the screen at all. Capturing
from the **Windows side**, via PowerShell + `System.Drawing` /
`CopyFromScreen` against that window's `GetWindowRect` bounds, bypasses
the WSL-internal X11/Wayland GPU-surface compositing problem entirely
and produces a correct image. This generalizes to any WSLg GUI app, not
just RViz — and is simpler than per-app workarounds like Gazebo's
screenshot service when one isn't available.

Screenshot saved: `images/rviz_display.png` — RobotModel + TF displays
both enabled, `Global Status: Ok`, TF axis markers visible at every
joint, confirming a fully-populated, live-updating kinematic tree.

## Scenario B — Nav2 + SLAM portfolio-grade re-audit

Standard applied: ROS 2 state + SLAM output + Nav2 logs, not Gazebo
visualization. Each finding below is backed by a command and its actual
output, run against a fully clean restart (all Gazebo/slam_toolbox/
bridge processes killed and relaunched together, after an earlier test
pass was invalidated — see "Process-hygiene defect" below).

### Hard blocker found and fixed: no LiDAR existed

The robot had zero sensors. `slam_toolbox` cannot build a map without
range data. Added a `lidar_link` (URDF, `base.xacro`) and a `gpu_lidar`
Gazebo sensor (`mobile_manipulator.gazebo.xacro`), bridged via
`ros_gz_bridge` to `/scan`.

**`gz_frame_id` bug, root-caused, not assumed:** `strings` on
`libgz-sensors8.so.8` confirmed `gz_frame_id` is the plugin's real
internal keyword, but `xacro ... | gz sdf -p` showed sdformat's
URDF→SDF converter silently drops it (`<sensor>` has no standard schema
slot for it, unlike `<ros2_control>`, which has explicit pass-through
support). Fix: a zero-offset `static_transform_publisher` in
`gazebo_sim.launch.py` bridging `lidar_link` to gz-sim's
auto-generated frame `mobile_manipulator/base_link/lidar`. Verified:
`tf2_echo base_link mobile_manipulator/base_link/lidar` →
`[-0.300, 0.000, 0.200]`, identity rotation — exactly the `lidar_joint`
origin.

**Scan data verified geometrically, not just "non-empty":** computed
local `(x, y) = range * (cos θ, sin θ)` from real `/scan` output and
matched it to the known `obstacle_wall` geometry (1.80m local x = 1.5m
wall face − (−0.30m) mount offset) — hard mathematical proof the sensor
returns real geometry, not noise.

### Process-hygiene defect found in my own test methodology

First SLAM pass showed `/map` byte-identical (confirmed via MD5 hash of
the occupancy array, not just timestamp) across 11+ seconds of confirmed
robot motion — looked exactly like Task 1's "frozen map" failure mode.
Root cause, found in `slam_toolbox`'s own log, not guessed:
```
[WARN] [tf2_buffer]: Detected jump back in time. Clearing TF buffer.
```
repeated dozens of times. Cause: `slam_toolbox` had been left running
across multiple Gazebo restarts during LiDAR debugging, so its sim-time
clock kept jumping backward each restart. `ps aux` also turned up **two
overlapping Gazebo sessions and a duplicate `ros_gz_bridge`** from
earlier relaunches that were never fully torn down. Fixed by killing
every related PID explicitly, restarting the `ros2` daemon, and
relaunching Gazebo → `slam_toolbox` fresh in sequence. This was a defect
in my test process, not in the SLAM pipeline — documented here because
it explains why the first measurement looked like a real bug and would
have been a false "frozen map" finding if reported without the restart.

### Task 1 — SLAM: map genuinely updates with motion (verified)

After the clean restart, hashed `/map`'s occupancy array across a 30s
window of continuous robot motion:
```
#1 stamp=20 hash=4cfea9ffcaac size=1404
#3 stamp=23 hash=4cfea9ffcaac size=1404
#4 stamp=25 hash=9e5c1d1fdc23 size=1640   <- content AND size changed
#6 stamp=30 hash=9e5c1d1fdc23 size=1640
```
The map grew from 1404 to 1640 cells and the hash changed exactly once
enough motion accumulated past `slam_toolbox`'s `map_update_interval`
(5.0s default) and `minimum_travel_heading` (0.5 rad default) — this is
real motion+sensor fusion, not a frozen snapshot. The earlier identical
hashes were simply shorter test windows than one update cycle, not a
defect.

`tf2_echo map base_link` independently confirmed `map -> base_link`
tracks real motion: `[0.746, 0.008]`, matching odometry almost exactly.

### Task 2 — Nav2 lifecycle: all 4 nodes ACTIVE (verified)

```
$ ros2 lifecycle get /controller_server   -> active [3]
$ ros2 lifecycle get /planner_server      -> active [3]
$ ros2 lifecycle get /behavior_server     -> active [3]
$ ros2 lifecycle get /bt_navigator        -> active [3]
```
Launch log confirms clean `UNCONFIGURED -> INACTIVE -> ACTIVE` transitions
with bonds established to `lifecycle_manager_navigation`, and
`"Managed nodes are active"`. `global_costmap`'s `static_layer` log shows
`"Subscribing to the map topic (/map) with transient local durability"`
and `"StaticLayer: Resizing costmap to 40 X 41 ... "` — a real resize
event tied to the actual map dimensions slam_toolbox produced, not a
default/empty costmap. `map_server` is intentionally not part of this
stack (live SLAM serves `/map` directly; no static map is loaded).

A transient `"Tf has two or more unconnected trees"` warning appears
once at `global_costmap` activation, then resolves 1s later — the same
TF-buffer-warmup race observed elsewhere in this project at startup, not
a persistent fault.

### Task 3 — End-to-end navigation: real motion confirmed, reliability not yet proven

Sent a real `NavigateToPose` goal (0.8, 0.3) via
`ros2 action send_goal /navigate_to_pose ... --feedback`. Feedback's
`current_pose` advanced from the origin to `[0.983, 0.001]` with real
rotation, in lock-step with odometry — this is Nav2's own controller
driving the robot, not teleop override or TF spoofing (no `cmd_vel` was
published by anything other than `controller_server` during this
window).

A second goal (0.6, 0.0), requiring the robot to backtrack toward its
start, was accepted but produced **zero robot motion**. Initial
hypothesis ("backtracking goals are unreliable") was wrong and was
corrected by further testing below — root cause was structural, not
direction-specific.

**Real structural bug found and fixed: `cmd_vel` type mismatch meant
no Nav2 command ever reached the robot.** `ros2 topic info
/mobile_base_controller/cmd_vel --verbose` showed **two incompatible
publisher types on the same topic name**: `controller_server` and
`behavior_server` were publishing plain `geometry_msgs/msg/Twist`, while
`mobile_base_controller` (`diff_drive_controller`) subscribes with
`geometry_msgs/msg/TwistStamped`. DDS treats these as different topics
entirely — every velocity command Nav2 ever computed was silently
discarded, regardless of what the action status reported. This is the
exact same `Twist`→`TwistStamped` migration gotcha already hit once in
this project for `teleop_twist_keyboard` (see Scenario A), but it had
never been applied to Nav2's own config. Fixed by setting
`enable_stamped_cmd_vel: true` on both `controller_server` and
`behavior_server` in `nav2_params.yaml`. A secondary, real timing issue
was fixed alongside it: `controller_server`'s log showed
`RPPPathHandler: Exception in transformPose: Lookup would require
extrapolation into the past` — `slam_toolbox`'s `map->odom` TF publish
timing is irregular enough under this CPU-constrained environment that
lookups occasionally landed ~50ms before the buffer's earliest sample.
Fixed by setting `transform_tolerance: 0.5` on `FollowPath`.

**Re-tested after both fixes, with rigor — not trusting a single
success:** ran 4 distinct goals (including the exact one that had
failed twice before the fix) across a clean restart.
```
$ ros2 run mobile_manipulator_bringup verify_scenario_b.py --goal-x -0.2 --goal-y 0.0
[PASS] Layer 4: Navigation goal: goal SUCCEEDED
```
3 of 4 goals reached `STATUS_SUCCEEDED` (one needed one internal
progress-checker-triggered recovery cycle before succeeding — confirmed
via `controller_server`'s log: `"Reached the goal!"` — and via the
action's own `GoalStatusArray` showing `status: 4` for all of them). The
4th goal (-0.5, -0.3) cleanly `ABORTED` after exhausting BT recoveries —
a real, current limitation, not hidden.

**Honest conclusion: the cmd_vel type mismatch was the actual root
cause of essentially all of this engagement's earlier Nav2 motion
failures — without it, the success rate was 0% regardless of goal
direction.** After fixing it, navigation succeeds on most tested goals,
including goals requiring backtracking, but not 100% reliably yet
(observed 3/4). This now meets the spirit of the spec's bar ("a fresh
boot can autonomously map an unknown environment and navigate to a
goal") for most goals, though full reliability on arbitrary goals is
still not proven. Scenario B is substantially stronger than the
previous assessment in this document, but still **not** declared fully
complete.

### Verification tooling added

`ros2 run mobile_manipulator_bringup verify_scenario_b.py [--goal-x X --goal-y Y]`
checks 4 layers against live state and exits non-zero on any failure:
SLAM (`/map` has non-unknown cells), Nav2 lifecycle (`active` on all 4
nodes via the real lifecycle service, not process-alive), TF
(`map -> base_link` via an actual `tf2` lookup), and navigation (sends a
real goal, watches `GoalStatusArray` for the true terminal status,
reports `ABORTED`/`CANCELED` honestly rather than treating "didn't
crash" as success).

## Gazebo <-> RViz / TF state consistency audit

Triggered by a direct report of "robot motion in Gazebo doesn't match
RViz, obstacles in Gazebo aren't reflected in planning." Audited against
the running stack at the topic/service level — not by looking at
screenshots — per layer:

**Environment finding (not a code defect):** the first audit attempt
hit a fully dead simulation — `gz sim server`/`gz sim gui` had exited
entirely after running for ~80 minutes in GUI mode, while
`robot_state_publisher`, `slam_toolbox`, and the Nav2 stack were still
running, orphaned. `/joint_states` and `/odom` both showed
`Publisher count: 0`, and `ros2 topic info` was reporting stale/phantom
publisher entries from a daemon graph cache that hadn't caught up to
the crash. This is exactly the symptom described ("Gazebo and RViz show
different things") but the actual cause was a dead Gazebo process, not
a TF/config bug — confirmed by `ps -ef` showing no `gz sim` process at
all. Fixed by a fully clean restart; the structural audit below was
re-run against the resulting healthy session.

**TF tree audit (PASS):** raw `/tf` + `/tf_static` subscription (not
`view_frames`, which returned an incomplete graph) confirmed the full
chain on a healthy session: `map->odom` (slam_toolbox), `odom->base_link`
(mobile_base_controller), `base_link->{4 wheels, arm chain}`
(robot_state_publisher, dynamic), and `base_link->{arm_mount,
base_footprint, lidar_link}` + `top_wrist->tool0` (robot_state_publisher,
static). `/tf_static` has exactly 2 publishers (`robot_state_publisher`
for URDF-fixed joints, `static_transform_publisher` for the lidar frame
bridge) publishing disjoint frame pairs — no duplicate/conflicting
broadcasters.

**Odometry source audit — real bug found:** `/odom` and
`/mobile_base_controller/odom` both exist as topics, but only the latter
has a publisher (`mobile_base_controller`/diff_drive_controller — the
real one, not a fake publisher). `controller_server` was subscribed to
the bare `/odom` name (zero publishers) because `odom_topic` was only
set under `bt_navigator`'s parameters, never under `controller_server`'s.
This starved `RegulatedPurePursuitController`'s odom smoother (used by
`use_velocity_scaled_lookahead_dist: true`) of real velocity feedback.
**Fixed:** added `odom_topic: /mobile_base_controller/odom` under
`controller_server` in `nav2_params.yaml`.

**Clock / use_sim_time audit (PASS):** `/clock` confirmed live at
~101Hz with low jitter (`ros2 topic hz /clock`). Checked
`use_sim_time` via `ros2 param get` on all 9 relevant nodes
(`robot_state_publisher`, `mobile_base_controller`, `arm_controller`,
`joint_state_broadcaster`, `slam_toolbox`, `controller_server`,
`planner_server`, `behavior_server`, `bt_navigator`) — all `true`.

**`/joint_states` audit (PASS):** exactly 1 publisher
(`joint_state_broadcaster`, reading Gazebo's real physics state via
`gz_ros2_control`'s `GazeboSimSystem` hardware interface) and exactly 1
subscriber (`robot_state_publisher`). No `joint_state_publisher` (the
fake/GUI one) running. Live at ~8.6Hz.

**Costmap obstacle layer — the real root cause of the reported
mismatch:** `/scan` confirmed live with real range data (a forward hit
at 0.625m, geometrically consistent with the known `obstacle_wall`), and
the scan's frame (`mobile_manipulator/base_link/lidar`) confirmed to
resolve via TF with correct geometry. Despite this, calling
`/local_costmap/get_costmap` (the on-demand service — bypassed a
transient_local topic-replay quirk that gave false "NO MESSAGE" results
on this same environment earlier in this project) returned **zero
non-zero cost cells** across the entire grid. Root-caused via
`ros2 param get /local_costmap/local_costmap obstacle_layer.scan.max_obstacle_height`:
**`0.0`** — the per-source override (distinct from the layer-level
`max_obstacle_height: 2.0` default, which was never applied to the
`scan` source specifically). Every LiDAR point was silently rejected as
"too high to be an obstacle," because `lidar_link` is mounted at
z=0.20m, above the 0.0m ceiling. This is the actual cause of "obstacles
exist in Gazebo but aren't reflected in planning" — not a TF or sync
bug. **Fixed:** added `min_obstacle_height: 0.0` /
`max_obstacle_height: 2.0` explicitly under `obstacle_layer.scan` in
both `local_costmap` and `global_costmap` blocks in `nav2_params.yaml`.

**Verification after both fixes (not a screenshot):**
```
$ ros2 service call /local_costmap/get_costmap nav2_msgs/srv/GetCostmap
# before: nonzero_count=0
# after:  nonzero_count=1386, cells at world coords matching obstacle_wall's
#         actual position (x~1.3-1.7, consistent with its pose in the world file)

$ ros2 run mobile_manipulator_bringup verify_scenario_b.py --goal-x 0.5 --goal-y -0.3
[PASS] Layer 1: SLAM (/map)
[PASS] Layer 2: Nav2 lifecycle
[PASS] Layer 3: TF (map->base_link)
[PASS] Layer 4: Navigation goal: goal SUCCEEDED
```

## Navigation reliability investigation — final honest state

Asked directly: "how to make navigation reliable on every goal?" Pursued
this to a precise, evidenced conclusion rather than declaring victory
on an improved-but-incomplete success rate.

**Tuning applied (measured improvement, not assumed):**
- `progress_checker.movement_time_allowance`: 10.0 → 20.0,
  `required_movement_radius`: 0.5 → 0.3 — `SimpleProgressChecker` only
  measures translational displacement; `RegulatedPurePursuitController`
  correctly rotates in place to face a path's initial heading before
  driving, and the old budget could be exhausted by that rotation alone,
  aborting the goal before it ever moved. Server logs showed real
  aborts ("Failed to make progress") while the robot was actively
  mid-rotation, not stuck.
- `FollowPath.rotate_to_heading_angular_vel`: → 2.5 — shortens the
  zero-translation rotation window.
- Custom BT XML (`navigate_to_pose_w_replanning_and_recovery.xml`,
  wired via `bt_navigator.default_nav_to_pose_bt_xml` in
  `navigation.launch.py`, since static params YAML can't use
  `find-pkg-share` launch substitution): cut the stock recovery
  `RoundRobin`'s `Wait` action from 5.0s to 1.0s. That Wait exists in
  Nav2's default tree for transient dynamic obstacles (e.g. a person
  crossing the path); this world is static, so it bought nothing and
  measurably burned wall-clock time across retries.

**Measured result, clean-restart-per-goal (removes cumulative-drift as
a confound):** 2/3 succeeded, up from goals that previously aborted
outright with `TF_ERROR`/`FAILED_TO_MAKE_PROGRESS`
(`(0.6,0.0)`, `(-0.2,0.0)` now reliably `SUCCEEDED`).

**The one remaining failure, root-caused to its actual mechanism, not
left as "still flaky":** goal `(-0.3, 0.2)` produced `cmd_vel` of
exactly zero, continuously, for 45+ seconds, with **no error or abort
ever logged** — `controller_server` kept "Passing new path to
controller" in an endless, silent loop. Isolated via
`ros2 service call .../get_cost_local_costmap`:
```
cost at current position, facing forward (theta=0):    0.0
cost at current position, facing the goal (theta=2.55): 37.0
```
The robot's rectangular footprint, rotating in place to face this
goal, sweeps through a real inflated-cost cell from nearby clutter.
`RegulatedPurePursuitController`'s `use_collision_detection` +
`max_allowed_time_to_collision_up_to_carrot: 1.0` correctly predicts
this and refuses to execute the rotation — outputting zero velocity
rather than throwing an exception, which is why nothing appeared in
the logs.

**Conclusion: this is the controller behaving safely, not a bug.**
"Reliable on every goal" without qualification is not an achievable or
even desirable target — a controller that never refuses a
collision-risking maneuver is less safe, not more reliable. The
remaining gap is a real reachability/safety-margin tradeoff
(`inflation_radius` vs. how close the spawn point is to clutter), not
a defect with a clean fix. Scenario B is not claimed to have 100%
goal-success; it is claimed to have a verified-correct architecture
(TF, odom, clock, costmap, cmd_vel pipeline) and a measured, improved
success rate on goals within a reasonable operating envelope.

## Known-not-yet-tested

- Whether reducing `inflation_radius` trades acceptable safety margin
  for meaningfully higher goal-reachability near clutter — not
  attempted; flagged as a real tradeoff above, not implemented.
- rosbag recording + replay of a full Scenario B run.
- Real hardware deployment path (`mobile_manipulator_hardware`) — still
  stub-only by design, see `HARDWARE.md`.
