cmake_minimum_required(VERSION 3.8)
project(fpga-interface)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
install(DIRECTORY config/
  DESTINATION share/${PROJECT_NAME}/config
)
install(PROGRAMS
  scripts/fpga_interface_node.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
