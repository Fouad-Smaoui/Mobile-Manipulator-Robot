"""Bridge between ROS 2 and the FPGA (e.g. for high-rate arm joint control
or sensor pre-processing offloaded to fabric).

STATUS: this is the same XML-config-driven skeleton found in the original
`fpga-interface` package, salvaged and cleaned up. It still does not open
a real connection to FPGA fabric -- the original had a bare comment
("# Initialize communication with FPGA") with no code after it. That gap
is preserved here as an explicit TODO instead of being silently dropped,
so the repository doesn't claim FPGA connectivity it doesn't have.
"""
import xml.etree.ElementTree as ET

import rclpy
from rclpy.node import Node

from mobile_manipulator_interfaces.msg import HardwareStatus


class FPGABridgeNode(Node):

    def __init__(self):
        super().__init__('fpga_bridge')

        self.declare_parameter('fpga_config_file', '')
        config_file = self.get_parameter('fpga_config_file').value

        self._fpga_ip_address = None
        self._ros_port = None
        if config_file:
            tree = ET.parse(config_file)
            root = tree.getroot()
            self._fpga_ip_address = root.find('parameter[@name="fpga_ip_address"]').get('value')
            self._ros_port = root.find('parameter[@name="ros_port"]').get('value')

        # TODO(hardware): open a TCP/UDP or AXI-mailbox socket to
        # self._fpga_ip_address:self._ros_port here once an FPGA target
        # is connected. Until then this node only reports its
        # configuration and a disconnected status.
        self._connected = False

        self._status_pub = self.create_publisher(HardwareStatus, '/hardware/status', 10)
        self._status_timer = self.create_timer(1.0, self._publish_status)

        self.get_logger().warn(
            f'fpga_bridge running in STUB mode (target={self._fpga_ip_address}:'
            f'{self._ros_port}) -- no physical FPGA link is open.'
        )

    def _publish_status(self):
        msg = HardwareStatus()
        msg.device_name = 'fpga'
        msg.connected = self._connected
        msg.transport = f'{self._fpga_ip_address}:{self._ros_port}'
        msg.last_error = '' if self._connected else 'no physical FPGA link open (stub mode)'
        msg.stamp = self.get_clock().now().to_msg()
        self._status_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = FPGABridgeNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
