#!/usr/bin/env python3
import rclpy
from my_custom_pkg.module_to_import import MyNode

def main (args=None):
    rclpy.init(args=args) # initialize ROS2 communications
    node = MyNode()    #create node inherited from node class rclpy
     #run some stuffs
    rclpy.spin(node) # node kept alive until kill it   
    rclpy.shutdown() #destroy node and shutdown ROS2 communications 
        
    
if __name__ == '__main__':
    main()
    