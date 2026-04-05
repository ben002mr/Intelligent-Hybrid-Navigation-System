import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import Odometry
from tf_transformations import euler_from_quaternion

import math


class HybridNavigator(Node):

    def __init__(self):
        super().__init__('hybrid_navigator')

        # Goal position
        self.goal_x = 2.0
        self.goal_y = 0.0

        self.current_x = 0.0
        self.current_y = 0.0

        self.front_distance = 999.0
        self.ranges = [10.0] * 360
        self.yaw = 0.0

        # Subscribers
        self.create_subscription(LaserScan, '/scan', self.scan_callback, 10)
        self.create_subscription(Odometry, '/odom', self.odom_callback, 10)

        # Publisher
        self.publisher = self.create_publisher(Twist, '/cmd_vel', 10)

        # Timer (control loop)
        self.create_timer(0.1, self.control_loop)

    def scan_callback(self, msg):
        self.ranges = msg.ranges
        front = min(msg.ranges[:30] + msg.ranges[-30:])
        self.front_distance = front

    def odom_callback(self, msg):
        self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y

        # Get orientation (quaternion)
        q = msg.pose.pose.orientation

        # Convert to yaw
        _, _, self.yaw = euler_from_quaternion([
            q.x,
            q.y,
            q.z,
            q.w
        ])

    def control_loop(self):
        twist = Twist()

        if not hasattr(self, 'ranges'):
            return

        # Distance to goal
        dx = self.goal_x - self.current_x
        dy = self.goal_y - self.current_y
        distance = math.sqrt(dx**2 + dy**2)
        angle_to_goal = math.atan2(dy, dx)

        # 🧠 PRIORITY 1: Obstacle Avoidance
        # Split scan into left and right
        left = min(self.ranges[30:90])
        right = min(self.ranges[-90:-30])

        if self.front_distance < 0.35:
            twist.linear.x = 0.05

            if left > right:
                twist.angular.z = 0.3   # turn left
                self.get_logger().info("Avoiding → LEFT")
            else:
                twist.angular.z = -0.3  # turn right
                self.get_logger().info("Avoiding → RIGHT")

        # 🧠 PRIORITY 2: Goal Seeking
        elif distance > 0.1:

            angle_error = angle_to_goal - self.yaw
            angle_error = math.atan2(math.sin(angle_error), math.cos(angle_error))

            # If not facing goal → rotate
            if abs(angle_error) > 0.2:
                twist.linear.x = 0.0
                twist.angular.z = 0.5 if angle_error > 0 else -0.5
                self.get_logger().info(f"Rotating to goal: {angle_error:.2f}")

            # If aligned → move forward
            else:
                twist.linear.x = 0.2
                twist.angular.z = 0.0
                self.get_logger().info(f"Moving to goal: {distance:.2f}")

        else:
            twist.linear.x = 0.0
            twist.angular.z = 0.0
            self.get_logger().info("Goal reached 🎯")

        self.publisher.publish(twist)


def main(args=None):
    rclpy.init(args=args)
    node = HybridNavigator()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()