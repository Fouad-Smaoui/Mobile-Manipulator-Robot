import xml.etree.ElementTree as ET
import rclpy
from rclpy.node import Node

class FPGAInterfaceNode(Node):
    def __init__(self):
        super().__init__('fpga_interface_node')
        # Load XML configuration
        config_file = self.declare_parameter('fpga_config_file').get_parameter_value().string_value
        tree = ET.parse(config_file)
        root = tree.getroot()
        # Extract parameters from XML
        self.fpga_ip_address = root.find('parameter[@name="fpga_ip_address"]').get('value')
        self.ros_port = root.find('parameter[@name="ros_port"]').get('value')
        # Initialize communication with FPGA

def main(args=None):
    rclpy.init(args=args)
    node = FPGAInterfaceNode()
    rclpy.spin(node)
    rclpy.shutdown()
