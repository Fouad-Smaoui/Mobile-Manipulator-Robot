#include "rclcpp/rclcpp.hpp"

namespace my_namespace {



    class MotorController : public rclcpp::Node
    {
        public:
        MotorController(const rclcpp::NodeOptions &options) : Node("motor_controller", options)
        {
            RCLCPP_INFO(this->get_logger(), "Hello");

        }
        private:
    };
}