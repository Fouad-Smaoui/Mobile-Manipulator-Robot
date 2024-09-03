#include "rclcpp/rclcpp.hpp"
#include "rcl_interfaces/msg/set_parameters_result.hpp"

class TestParamsCallback : public rclcpp::Node {
public:
    TestParamsCallback() : Node("test_params_rclcpp") {
        // Declare parameters with appropriate types
        this->declare_parameter<std::string>("motor_device_port", "/dev/ttyUSB0");
        this->declare_parameter<int>("control_loop_frequency", 10); // Example default value
        this->declare_parameter<bool>("simulation_mode", false);

        // Retrieve initial parameter values
        motor_device_port_ = this->get_parameter("motor_device_port").as_string();
        control_loop_frequency_ = this->get_parameter("control_loop_frequency").as_int();
        simulation_mode_ = this->get_parameter("simulation_mode").as_bool();

        // Set up parameter change callback
        params_callback_handle_ = this->add_on_set_parameters_callback(
            std::bind(&TestParamsCallback::paramsCallback, this, std::placeholders::_1));
    }

private:
    // Parameter callback to handle dynamic parameter changes
    rcl_interfaces::msg::SetParametersResult paramsCallback(const std::vector<rclcpp::Parameter> &params) {
        rcl_interfaces::msg::SetParametersResult result;
        result.successful = true;
        result.reason = "success";

        for (const auto &param : params) {
            if (param.get_name() == "control_loop_frequency") {
                int frequency = param.as_int();
                if (frequency >= 0 && frequency <= 100) { // Validating the range
                    control_loop_frequency_ = frequency;
                } else {
                    result.successful = false;
                    result.reason = "control_loop_frequency must be between 0-100";
                }
            } else if (param.get_name() == "motor_device_port") {
                motor_device_port_ = param.as_string();
            } else if (param.get_name() == "simulation_mode") {
                simulation_mode_ = param.as_bool();
            }
        }

        return result;
    }

    std::string motor_device_port_;
    int control_loop_frequency_;
    bool simulation_mode_;
    OnSetParametersCallbackHandle::SharedPtr params_callback_handle_;
};

int main(int argc, char **argv) {
    rclcpp::init(argc, argv);
    auto node = std::make_shared<TestParamsCallback>();
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}
