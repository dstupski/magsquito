#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32
from uldaq import get_daq_device_inventory, DaqDevice, InterfaceType, AiInputMode, AInFlag


class AnalogPublisher(Node):
    def __init__(self):
        super().__init__('analog_publisher')

        # Initialize DAQ device
        devices = get_daq_device_inventory(InterfaceType.USB)
        if not devices:
            self.get_logger().error("No USB DAQ devices found.")
            return

        self.daq_device = DaqDevice(devices[0])  # Connect to the first available device
        self.ai_device = self.daq_device.get_ai_device()
        self.daq_device.connect()

        # Get device range (modify based on your hardware)
        ai_info = self.ai_device.get_info()
        self.ai_range = list(ai_info.get_ranges(AiInputMode.SINGLE_ENDED))[0]

        # Create individual publishers for each analog input
        self.num_channels = 8  # Adjust as needed
        self.ai_publishers = []

        for ch in range(self.num_channels):
            topic_name = f'/analog_input/AI{ch}'
            pub = self.create_publisher(Float32, topic_name, 10)
            self.ai_publishers.append(pub)

        # Publish at 100 Hz
        self.timer = self.create_timer(0.01, self.publish_analog_data)

    def publish_analog_data(self):
        if not self.daq_device.is_connected():
            self.get_logger().error("DAQ device not connected.")
            return

        flags = AInFlag.DEFAULT

        for ch in range(self.num_channels):
            try:
                voltage = self.ai_device.a_in(ch, AiInputMode.SINGLE_ENDED, self.ai_range, flags)
                msg = Float32()
                msg.data = voltage
                self.ai_publishers[ch].publish(msg)
            except Exception as e:
                self.get_logger().error(f"Error reading AI{ch}: {e}")

    def destroy_node(self):
        if self.daq_device.is_connected():
            self.daq_device.disconnect()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = AnalogPublisher()
    if node.daq_device.is_connected():
        rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()