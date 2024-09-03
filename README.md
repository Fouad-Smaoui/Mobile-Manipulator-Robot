# ROS 2 Mobile Manipulator

## Overview

Welcome to the ROS 2 Mobile Manipulator project! This repository provides a comprehensive set of tools and configurations to operate and control a mobile manipulator robot using ROS 2. The mobile manipulator integrates a mobile base with an articulated robotic arm, making it suitable for various tasks such as object manipulation, navigation, and automated tasks in dynamic environments.

### Features

- **Mobile Base Integration**: Interface with a mobile base for autonomous navigation.
- **Articulated Arm Control**: Manipulate objects with a robotic arm using inverse kinematics and trajectory planning.
- **Sensor Integration**: Utilize sensors like cameras and LIDAR for perception and environment mapping.
- **Simulation Support**: Test and develop algorithms in a simulated environment using Gazebo.
- **Navigation Stack**: Leverage the Nav2 stack for autonomous navigation and path planning.
- **Visualization**: Use RViz for visualization of robot states, sensor data, and planning.

## Prerequisites

Before you begin, ensure you have the following software installed:

- **ROS 2 Humble Hawksbill**: [Installation instructions](https://docs.ros.org/en/humble/Installation.html).
- **Colcon**: Build tool for ROS 2 workspaces. [Installation instructions](https://colcon.readthedocs.io/en/released/user/quick-start.html).
- **Python 3**: Required for various ROS 2 tools and scripts.
- **Gazebo**: For simulation purposes. [Installation instructions](https://gazebosim.org/tutorials?tut=install_ubuntu).
- **C++**: Required for building C++ nodes and libraries. Ensure you have a compatible compiler installed (e.g., GCC for Linux).
- **CMake**: Build system for configuring and generating build files. [Installation instructions](https://cmake.org/install/).
- **RViz**: Visualization tool for ROS. [Installation instructions](https://docs.ros.org/en/humble/Installation.html#rviz).
- **Nav2**: Navigation stack for autonomous robots. [Installation instructions](https://navigation.ros.org/).