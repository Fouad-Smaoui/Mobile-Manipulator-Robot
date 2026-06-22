from setuptools import find_packages, setup

package_name = 'mobile_manipulator_hardware'

setup(
    name=package_name,
    version='1.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/hardware_bringup.launch.py']),
        ('share/' + package_name + '/config', ['config/hardware_config.yaml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='fouad-smaoui',
    maintainer_email='fouad.smaoui@outlook.com',
    description='Real-hardware deployment bridges for the mobile manipulator (motor driver, FPGA).',
    license='CC0-1.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'motor_driver_bridge = mobile_manipulator_hardware.motor_driver_bridge_node:main',
            'fpga_bridge = mobile_manipulator_hardware.fpga_bridge_node:main',
        ],
    },
)
