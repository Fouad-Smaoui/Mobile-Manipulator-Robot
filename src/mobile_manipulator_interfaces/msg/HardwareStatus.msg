# Reported by every hardware bridge node (motor driver, FPGA, future sensors)
# so a single /hardware/status aggregation topic can show whether each
# physical link in the deployment chain is actually connected.

string device_name        # e.g. "motor_driver", "fpga"
bool connected             # true once the underlying transport (serial/ethernet) is open
string transport           # e.g. "/dev/ttyUSB0", "192.168.1.50:5005"
string last_error          # empty string if no error
builtin_interfaces/Time stamp
