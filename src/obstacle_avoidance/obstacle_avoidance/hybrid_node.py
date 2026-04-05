import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan
import numpy as np
import time


class SmartHybrid(Node):

    def __init__(self):
        super().__init__('smart_hybrid')

        self.scan_sub = self.create_subscription(
            LaserScan, '/scan', self.scan_callback, 10)

        self.nav_sub = self.create_subscription(
            Twist, '/cmd_vel_nav', self.nav_callback, 10)

        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        self.scan = None
        self.nav_cmd = Twist()

        # 🧠 STATE MACHINE
        self.state = "FORWARD"

        # 🧭 Direction memory
        self.turn_direction = 1  # 1 = left, -1 = right

        # ⏱️ Stuck detection
        self.last_clear_time = time.time()

    def nav_callback(self, msg):
        self.nav_cmd = msg

    def scan_callback(self, msg):
        self.scan = msg
        self.process()

    def process(self):
        if self.scan is None:
            return

        ranges = np.array(self.scan.ranges)
        ranges = np.where(np.isinf(ranges), 10.0, ranges)

        front = np.min(ranges[0:30].tolist() + ranges[-30:].tolist())
        left = np.min(ranges[60:120])
        right = np.min(ranges[240:300])

        cmd = Twist()

        SAFE = 0.5
        CRITICAL = 0.3

        now = time.time()

        # ========================
        # 🚨 ESCAPE MODE
        # ========================
        if self.state == "ESCAPE":
            cmd.linear.x = -0.1
            cmd.angular.z = 0.8 * self.turn_direction

            self.get_logger().error("🚨 ESCAPING")

            # exit escape after some time
            if now - self.last_clear_time > 2.0:
                self.state = "FORWARD"

            self.cmd_pub.publish(cmd)
            return

        # ========================
        # ⚠️ CRITICAL ZONE
        # ========================
        if front < CRITICAL:
            self.state = "ESCAPE"
            self.last_clear_time = now
            self.get_logger().error("🚨 TOO CLOSE → ESCAPE")
            return

        # ========================
        # ⚠️ AVOID MODE
        # ========================
        if front < SAFE:
            self.state = "AVOID"

            # choose direction ONCE
            if left > right:
                self.turn_direction = 1
            else:
                self.turn_direction = -1

            cmd.linear.x = 0.05
            cmd.angular.z = 0.5 * self.turn_direction

            self.get_logger().warn("⚠️ AVOIDING")

            self.cmd_pub.publish(cmd)
            return

        # ========================
        # ✅ FORWARD MODE
        # ========================
        self.state = "FORWARD"
        self.last_clear_time = now

        cmd = self.nav_cmd

        self.get_logger().info("✅ FOLLOWING NAV2")

        self.cmd_pub.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = SmartHybrid()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()