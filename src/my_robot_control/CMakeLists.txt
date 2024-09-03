cmake_minimum_required(VERSION 3.8)
project(my_robot_control)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)

add_executable(params_callback src/params_callback.cpp)
ament_target_dependencies(params_callback rclcpp)

install(TARGETS params_callback
  DESTINATION lib/${PROJECT_NAME})


ament_package()
