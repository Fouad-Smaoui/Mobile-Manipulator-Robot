from launch import LaunchDescription 
from launch_ros.actions import Node

def generate_launch_description():
    ld=LaunchDescription()
    
    talker_node = Node(
        package = "demo_nodes_cpp",
        executable = "talker",
        name = "my_talker",
        remappings = [
            ("chatter", "my_chatter")
        ],
        parameters=[
            {"param_name":200},
            {"param2":19}
        ]
    )
    listener_node = Node(
        package= "demo_nodes_py",
        executable = "listener",
        remappings=[
            ("chatter", "my_chatter")
        ]
    )
    
    ld.add_action(talker_node)
    ld.add_action(listener_node)
    
    return ld
