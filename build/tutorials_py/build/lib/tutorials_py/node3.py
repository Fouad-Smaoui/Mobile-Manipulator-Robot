#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from example_interfaces.msg import Float64

class Node3(Node):
    def __init__(self):
        super().__init__("node3")
        self.number_sub_ = self.create_subscription(Float64, "data_2",self.number_callback, 10)
        
    def number_callback(self, msg: Float64):
        self.get_logger().info("Received : " + str(msg.data))
        
        
def main (args=None):
    rclpy.init(args=args) # initialize ROS2 communications
    node = Node3()    #create node inherited from node class rclpy
     #run some stuffs
    rclpy.spin(node) # node kept alive until kill it   
    rclpy.shutdown() #destroy node and shutdown ROS2 communications 
        
    
if __name__ == '__main__':
    main()