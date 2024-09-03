#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.lifecycle import LifecycleNode, LifecycleState, TransitionCallbackReturn
from example_interfaces.msg import Int64

class MyNode(LifecycleNode):
    def __init__(self):
        super().__init__("my_node")
        self.get_logger().info("In constructor")
        self.pub_ = None
        self.timer_ = None
        
    def on_configure(self, state:LifecycleState):
        self.get_logger().info("In on_configure")
        self.pub_ = self.create_lifecycle_publisher(Int64, "number", 10)
        self.timer_ = self.create_timer(1.0, self.publish_number)
        self.timer_.cancel()
        return TransitionCallbackReturn.SUCCESS
    
    def on_cleanup(self,state: LifecycleState):
        self.get_logger().info("In on_cleanup")
        self.destroy_lifecycle_publisher(self.pub_)
        self.destroy_timer(self.timer_)
        return TransitionCallbackReturn.SUCCESS
    
    def on_activate(self, state: LifecycleState):
        self.get_logger().info("In on_activate")
        self.timer_.reset()
        return super().on_activate(state)
    
    def on_deactivate(self, state: LifecycleState):
        self.get_logger().info("In on_deactivate")
        self.timer_.cancel()
        return super().on_deactivate(state)
    
    def on_shutdown(self, state: LifecycleState):
        self.get_logger().info("In on_shutdown")
        self.destroy_lifecycle_publisher(self.pub_)
        self.destroy_timer(self.timer_)
        return TransitionCallbackReturn().SUCESS
    
    def publish_number(self):
        msg=Int64()
        msg.data = 5
        self.get_logger().info("Publish number")
        self.pub_.publish(msg)    
        
def main (args=None):
    rclpy.init(args=args) # initialize ROS2 communications
    node = MyNode()    #create node inherited from node class rclpy
     #run some stuffs
    rclpy.spin(node) # node kept alive until kill it   
    rclpy.shutdown() #destroy node and shutdown ROS2 communications 
        
if __name__ == '__main__':
    main()
        