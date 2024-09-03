#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from example_interfaces.msg import Float64

class Node2(Node):
    def __init__(self):
        super().__init__("node2")
        self.number_pub_ = self.create_publisher(Float64, "data_2", 10)
        self.number_sub_ = self.create_subscription(Float64, "data_1",self.number_callback,10)
        
    def number_callback(self, msg: Float64):
        number = msg.data
        new_msg = Float64()
        new_msg.data = number*2.0
        self.get_logger().info("Received : " + str(number) +", Publishing : " + str(new_msg.data))
        self.number_pub_.publish(new_msg)
        
def main (args=None):
    rclpy.init(args=args) # initialize ROS2 communications
    node = Node2()    #create node inherited from node class rclpy
     #run some stuffs
    rclpy.spin(node) # node kept alive until kill it   
    rclpy.shutdown() #destroy node and shutdown ROS2 communications 
        
    
if __name__ == '__main__':
    main()
    
