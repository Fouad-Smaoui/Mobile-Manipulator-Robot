cmake_minimum_required(VERSION 3.8)
project(my_custom_pkg)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclpy REQUIRED)
find_package(rclcpp_components REQUIRED)

add_library(motor_controller_component SHARED src/component_test.cpp)
ament_target_dependencies(motor_controller_component rclcpp rclcpp_components)
#Include cpp "include" directory
include_directories((include))

#Create cpp executables
add_executable(cpp_exe src/cpp_node.cpp)
ament_target_dependencies(cpp_exe rclcpp)

#Install cpp executables
install(TARGETS 
  motor_controller_component
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin 

  #cpp_exe
  #DESTINATION lib/${PROJECT_NAME}
)

#Install Py modules
ament_python_install_package(${PROJECT_NAME})

#Install py executables
install(PROGRAMS 
 scripts/composition.py
 DESTINATION lib/${PROJECT_NAME}
)

ament_package()
