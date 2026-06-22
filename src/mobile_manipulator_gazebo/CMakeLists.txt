cmake_minimum_required(VERSION 3.8)
project(mobile_manipulator_gazebo)

find_package(ament_cmake REQUIRED)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

install(
  DIRECTORY urdf worlds launch
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
