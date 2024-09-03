from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
#from launch.launch_description_sources import PythonLaunchDescriptionSource
#from launch_yaml.launch_description_sources import YAMLLaunchDescriptionSourceMLLaunchDescriptionSource
from launch_xml.launch_description_sources import XMLLaunchDescriptionSource
import os
from ament_index_python import get_package_share_directory

def generate_launch_description(): 
    ld = LaunchDescription()
    
    other_launch_file = IncludeLaunchDescription(
        XMLLaunchDescriptionSource( #change py or xml or yaml
            os.path.join(get_package_share_directory('my_robot_bringup'),
                    "launch/demo.launch.xml") #change extension py or xml or yaml
        )
    )
    ld.add_action(other_launch_file)
    return ld
