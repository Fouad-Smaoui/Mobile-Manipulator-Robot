// REFERENCE SKELETON -- not compiled, not registered via pluginlib.
//
// This is the shape the real ros2_control hardware plugin would take if
// this package were upgraded to a C++ ament_cmake_python hybrid. It is
// committed as a design artifact (per the project's hardware-deployment
// roadmap) rather than as working code, so it is kept under doc/reference
// instead of include/ -- it must not be mistaken for a built plugin.
//
// To make this real:
//   1. Move to include/mobile_manipulator_hardware/ + src/mobile_manipulator_system.cpp
//   2. Add hardware_interface, pluginlib, rclcpp_lifecycle deps to package.xml
//   3. Export via PLUGINLIB_EXPORT_CLASS and a mobile_manipulator_hardware.xml plugin
//      description, referenced from CMakeLists.txt's pluginlib_export_plugin_description_file()
//   4. Implement on_init/export_state_interfaces/export_command_interfaces/
//      read/write against the real motor driver (reuse motor_driver_bridge_node's
//      serial contract) and FPGA link (reuse fpga_bridge_node's protocol).

#pragma once
#include "hardware_interface/system_interface.hpp"

namespace mobile_manipulator_hardware
{

class MobileManipulatorSystem : public hardware_interface::SystemInterface
{
public:
  // hardware_interface::SystemInterface overrides:
  // CallbackReturn on_init(const hardware_interface::HardwareInfo & info) override;
  // std::vector<hardware_interface::StateInterface> export_state_interfaces() override;
  // std::vector<hardware_interface::CommandInterface> export_command_interfaces() override;
  // hardware_interface::return_type read(const rclcpp::Time &, const rclcpp::Duration &) override;
  // hardware_interface::return_type write(const rclcpp::Time &, const rclcpp::Duration &) override;
  //
  // read()  -> poll motor encoder + arm joint positions over the serial
  //            link opened by the pattern in motor_driver_bridge_node.py
  // write() -> push wheel velocity commands + arm position commands over
  //            the same link, and joint setpoints destined for the FPGA
  //            (high-rate path) over the link opened by fpga_bridge_node.py
};

}  // namespace mobile_manipulator_hardware
