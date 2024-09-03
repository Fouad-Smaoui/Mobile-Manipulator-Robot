// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from my_robot_interfaces:msg/TargetCoordinates.idl
// generated code does not contain a copyright notice

#ifndef MY_ROBOT_INTERFACES__MSG__DETAIL__TARGET_COORDINATES__BUILDER_HPP_
#define MY_ROBOT_INTERFACES__MSG__DETAIL__TARGET_COORDINATES__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "my_robot_interfaces/msg/detail/target_coordinates__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace my_robot_interfaces
{

namespace msg
{

namespace builder
{

class Init_TargetCoordinates_coordinates
{
public:
  explicit Init_TargetCoordinates_coordinates(::my_robot_interfaces::msg::TargetCoordinates & msg)
  : msg_(msg)
  {}
  ::my_robot_interfaces::msg::TargetCoordinates coordinates(::my_robot_interfaces::msg::TargetCoordinates::_coordinates_type arg)
  {
    msg_.coordinates = std::move(arg);
    return std::move(msg_);
  }

private:
  ::my_robot_interfaces::msg::TargetCoordinates msg_;
};

class Init_TargetCoordinates_name
{
public:
  Init_TargetCoordinates_name()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_TargetCoordinates_coordinates name(::my_robot_interfaces::msg::TargetCoordinates::_name_type arg)
  {
    msg_.name = std::move(arg);
    return Init_TargetCoordinates_coordinates(msg_);
  }

private:
  ::my_robot_interfaces::msg::TargetCoordinates msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::my_robot_interfaces::msg::TargetCoordinates>()
{
  return my_robot_interfaces::msg::builder::Init_TargetCoordinates_name();
}

}  // namespace my_robot_interfaces

#endif  // MY_ROBOT_INTERFACES__MSG__DETAIL__TARGET_COORDINATES__BUILDER_HPP_
