from setuptools import find_packages, setup

package_name = 'tutorials_py'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='fouadroboticist',
    maintainer_email='fouadroboticist@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': ['node1 = tutorials_py.node1:main',
            'node2 = tutorials_py.node2:main',
            'node3 = tutorials_py.node3:main',
        ],
    },
)
