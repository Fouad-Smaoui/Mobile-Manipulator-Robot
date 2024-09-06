from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='fpga-interface',
            executable='fpga_node_executable',  # Replace with your node executable name
            name='fpga_node',
            output='screen',
            parameters=[{'fpga_config_file': '/path/to/your/config/fpga_config.xml'}]
        ),
    ])
