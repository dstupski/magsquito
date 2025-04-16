#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32
import yaml

from uldaq import AnalogOutputDevice, InterfaceType, DaqDevice, DaqDeviceDescriptor, get_daq_device_inventory

class AnalogOutputNode(Node):

    def __init__(self, config_file: str):
        super().__init__('analog_output_node')

        # Load config
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)

        topic_name = config.get('subscriber_topic', 'analog_input')

        # Set up ULDAQ device
        self.device = self.setup_uldaq_device()
        self.ao_device = self.device.get_ao_device()
        self.ao_info = self.ao_device.get_info()
        self.channel = 0  # using channel 0 by default

        # Get output range (assuming single range supported)
        ranges = self.ao_info.get_ranges()
        self.min_v, self.max_v = ranges[0].min_val, ranges[0].max_val
        self.get_logger().info(f"Output range: {self.min_v}V to {self.max_v}V")

        # ROS2 Subscriber
        self.subscription = self.create_subscription(
            Float32,
            topic_name,
            self.listener_callback,
            10
        )
        self.get_logger().info(f'Subscribed to topic: {topic_name}')

    def setup_uldaq_device(self):
        devices = get_daq_device_inventory(InterfaceType.ANY)
        if not devices:
            raise RuntimeError("No DAQ devices found")

        descriptor = devices[0]
        self.get_logger().info(f'Connecting to device: {descriptor.product_name}')

        daq_device = DaqDevice(descriptor)
        daq_device.connect()
        return daq_device

    def listener_callback(self, msg: Float32):
        value = msg.data

        # Normalize and clamp
        voltage = min(max(value, 0.0), 1.0) * (self.max_v - self.min_v) + self.min_v
        self.get_logger().info(f'Outputting voltage: {voltage:.2f} V')

        # Output the voltage
        self.ao_device.a_out(self.channel, 0, voltage)

    def destroy_node(self):
        self.device.disconnect()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)

    import sys
    if len(sys.argv) < 2:
        print("Usage: ros2 run <your_package> analog_output_node.py <config.yaml>")
        return

    config_file = sys.argv[1]

    node = AnalogOutputNode(config_file)

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
