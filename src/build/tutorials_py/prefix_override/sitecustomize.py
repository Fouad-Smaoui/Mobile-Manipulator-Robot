import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/fouadroboticist/ros2_ws/src/Mobile-Manipulator-Robot/src/install/tutorials_py'
