cmake_minimum_required(VERSION 3.8)
project(mobile_manipulator_bringup)

find_package(ament_cmake REQUIRED)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

install(
  DIRECTORY launch config doc
  DESTINATION share/${PROJECT_NAME}
)

install(
  PROGRAMS scripts/pick_place_demo.py scripts/verify_scenario_c.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
