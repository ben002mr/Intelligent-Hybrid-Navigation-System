from setuptools import find_packages, setup

package_name = 'obstacle_avoidance'

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
    maintainer='ben',
    maintainer_email='benny2002@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'avoid = obstacle_avoidance.avoidance_node:main',
            'hybrid1 = obstacle_avoidance.waypoint_nav:main',
            'waypoint_nav2 = obstacle_avoidance.waypoint_nav2:main',
            'lidar = obstacle_avoidance.lidar_avoidance:main',
            'hybrid = obstacle_avoidance.hybrid_node:main',
        ],
    },
)
