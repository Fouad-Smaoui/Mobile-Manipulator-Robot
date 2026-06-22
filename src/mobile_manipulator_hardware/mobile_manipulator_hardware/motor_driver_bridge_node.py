"""Serial bridge between ros2_control and the base motor driver board.

STATUS: parameter contract + lifecycle implemented and salvaged from the
original repo's `params_callback.cpp` exercise; the actual serial
read/write to the motor controller (TODO markers below) is NOT
implemented because no physical driver board is connected. This node is
deliberately honest about that boundary rather than faking serial I/O --
see doc/HARDWARE.md for the wiring this would use once hardware exists.
"""
import rclpy
from rclpy.node import Node
from rcl_interfaces.msg import SetParametersResult

from mobile_manipulator_interfaces.msg import HardwareStatus


class MotorDriverBridgeNode(Node):

    def __init__(self):
        super().__init__('motor_driver_bridge')

        self.declare_parameter('motor_device_port', '/dev/ttyUSB0')
        self.declare_parameter('motor_baud_rate', 1_000_000)
        self.declare_parameter('control_loop_frequency_hz', 100)

        self._port = self.get_parameter('motor_device_port').value
        self._baud = self.get_parameter('motor_baud_rate').value
        self._freq = self.get_parameter('control_loop_frequency_hz').value

        self.add_on_set_parameters_callback(self._on_params_changed)

        self._status_pub = self.create_publisher(HardwareStatus, '/hardware/status', 10)
        self._status_timer = self.create_timer(1.0, self._publish_status)

        # TODO(hardware): open self._port at self._baud with pyserial once
        # a driver board is available, and replace _publish_status()'s
        # `connected=False` with the real link state.
        self._connected = False

        self.get_logger().warn(
            f'motor_driver_bridge running in STUB mode on {self._port} '
            f'@ {self._baud} baud -- no physical serial link is open.'
        )

    def _on_params_changed(self, params):
        result = SetParametersResult(successful=True)
        for param in params:
            if param.name == 'control_loop_frequency_hz' and not (0 < param.value <= 1000):
                result.successful = False
                result.reason = 'control_loop_frequency_hz must be in (0, 1000]'
        return result

    def _publish_status(self):
        msg = HardwareStatus()
        msg.device_name = 'motor_driver'
        msg.connected = self._connected
        msg.transport = self._port
        msg.last_error = '' if self._connected else 'no physical serial link open (stub mode)'
        msg.stamp = self.get_clock().now().to_msg()
        self._status_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = MotorDriverBridgeNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
