#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from example_interfaces.msg import Float64
import random

class Node1(Node):
    def __init__(self):
        super().__init__("node1")
        self.number_pub_ = self.create_publisher(Float64, "data_1",10)
        self.timer_ = self.create_timer(1.0, self.publish_number)
        
    def publish_number(self):
        msg= Float64()   
        msg.data = random.uniform(0.0, 10.0)
        self.get_logger().info("Publishing : " + str(msg.data))
        self.number_pub_.publish(msg)
        
def main (args=None):
    rclpy.init(args=args) # initialize ROS2 communications
    node = Node1()    #create node inherited from node class rclpy
     #run some stuffs
    rclpy.spin(node) # node kept alive until kill it   
    rclpy.shutdown() #destroy node and shutdown ROS2 communications 
        
    
if __name__ == '__main__':
    main()