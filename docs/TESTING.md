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

## Known-not-yet-tested

- Scenario B's full Nav2 + slam_toolbox path with an actual `2D Nav Goal`
  sent and a path executed.
- Real hardware deployment path (`mobile_manipulator_hardware`) — still
  stub-only by design, see `HARDWARE.md`.
