import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist


class HybridAvoidance(Node):

    def __init__(self):
        super().__init__('hybrid_avoidance')

        # Subscribe to Nav2 velocity
        self.nav_sub = self.create_subscription(
            Twist,
            '/cmd_vel_nav',
            self.nav_callback,
            10)

        # Subscribe to LiDAR
        self.scan_sub = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            10)

        # Publisher to robot
        self.publisher = self.create_publisher(Twist, '/cmd_vel', 10)

        self.current_nav_cmd = Twist()
        self.front = float('inf')
        self.front_left = float('inf')
        self.front_right = float('inf')

    def get_min(self, data):
        valid = [r for r in data if r > 0.0]
        return min(valid) if valid else float('inf')

    def scan_callback(self, msg):
        ranges = msg.ranges
        size = len(ranges)

        self.front = self.get_min(ranges[2*size//5:3*size//5])
        self.front_left = self.get_min(ranges[3*size//5:4*size//5])
        self.front_right = self.get_min(ranges[size//5:2*size//5])

    def nav_callback(self, msg):
        self.current_nav_cmd = msg

        twist = Twist()

        # 🚨 OVERRIDE LOGIC (YOUR AI)
        if self.front < 0.6:
            self.get_logger().info("🛑 Override: obstacle ahead")

            twist.linear.x = 0.0

            if self.front_left > self.front_right:
                twist.angular.z = 0.6
            else:
                twist.angular.z = -0.6

        elif self.front_left < 0.5:
            self.get_logger().info("⚠️ Adjust right")
            twist.linear.x = 0.05
            twist.angular.z = -0.4

        elif self.front_right < 0.5:
            self.get_logger().info("⚠️ Adjust left")
            twist.linear.x = 0.05
            twist.angular.z = 0.4

        else:
            # ✅ NORMAL NAV2 CONTROL
            twist = self.current_nav_cmd

        self.publisher.publish(twist)


def main(args=None):
    rclpy.init(args=args)
    node = HybridAvoidance()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()