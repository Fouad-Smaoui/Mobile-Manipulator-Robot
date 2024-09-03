// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from my_robot_interfaces:msg/TargetCoordinates.idl
// generated code does not contain a copyright notice

#ifndef MY_ROBOT_INTERFACES__MSG__DETAIL__TARGET_COORDINATES__STRUCT_HPP_
#define MY_ROBOT_INTERFACES__MSG__DETAIL__TARGET_COORDINATES__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


// Include directives for member types
// Member 'coordinates'
#include "geometry_msgs/msg/detail/point__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__my_robot_interfaces__msg__TargetCoordinates __attribute__((deprecated))
#else
# define DEPRECATED__my_robot_interfaces__msg__TargetCoordinates __declspec(deprecated)
#endif

namespace my_robot_interfaces
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct TargetCoordinates_
{
  using Type = TargetCoordinates_<ContainerAllocator>;

  explicit TargetCoordinates_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : coordinates(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->name = "";
    }
  }

  explicit TargetCoordinates_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : name(_alloc),
    coordinates(_alloc, _init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->name = "";
    }
  }

  // field types and members
  using _name_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _name_type name;
  using _coordinates_type =
    geometry_msgs::msg::Point_<ContainerAllocator>;
  _coordinates_type coordinates;

  // setters for named parameter idiom
  Type & set__name(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->name = _arg;
    return *this;
  }
  Type & set__coordinates(
    const geometry_msgs::msg::Point_<ContainerAllocator> & _arg)
  {
    this->coordinates = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    my_robot_interfaces::msg::TargetCoordinates_<ContainerAllocator> *;
  using ConstRawPtr =
    const my_robot_interfaces::msg::TargetCoordinates_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<my_robot_interfaces::msg::TargetCoordinates_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<my_robot_interfaces::msg::TargetCoordinates_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      my_robot_interfaces::msg::TargetCoordinates_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<my_robot_interfaces::msg::TargetCoordinates_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      my_robot_interfaces::msg::TargetCoordinates_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<my_robot_interfaces::msg::TargetCoordinates_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<my_robot_interfaces::msg::TargetCoordinates_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<my_robot_interfaces::msg::TargetCoordinates_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__my_robot_interfaces__msg__TargetCoordinates
    std::shared_ptr<my_robot_interfaces::msg::TargetCoordinates_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__my_robot_interfaces__msg__TargetCoordinates
    std::shared_ptr<my_robot_interfaces::msg::TargetCoordinates_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const TargetCoordinates_ & other) const
  {
    if (this->name != other.name) {
      return false;
    }
    if (this->coordinates != other.coordinates) {
      return false;
    }
    return true;
  }
  bool operator!=(const TargetCoordinates_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct TargetCoordinates_

// alias to use template instance with default allocator
using TargetCoordinates =
  my_robot_interfaces::msg::TargetCoordinates_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace my_robot_interfaces

#endif  // MY_ROBOT_INTERFACES__MSG__DETAIL__TARGET_COORDINATES__STRUCT_HPP_
