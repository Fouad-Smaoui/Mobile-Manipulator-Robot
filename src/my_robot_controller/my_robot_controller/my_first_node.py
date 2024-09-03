#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from my_robot_interfaces.msg import TargetCoordinates
from my_robot_interfaces.srv import SetLed

class MyNode(Node):
    def __init__(self):
        super().__init__("first_node")
        self.counter_ =0
        #self.get_logger().info("Hello from ROS2")
        self.create_timer(1.0, self.timer_callback)
    def timer_callback(self):
        self.get_logger().info("Hello"+str(self.counter_))
        self.counter_ +=1
def main (args=None):
    rclpy.init(args=args) # initialize ROS2 communications
    node = MyNode()    #create node inherited from node class rclpy
     #run some stuffs
    rclpy.spin(node) # node kept alive until kill it   
    rclpy.shutdown() #destroy node and shutdown ROS2 communications 
        
    
if __name__ == '__main__':
    main()
    