import numpy as np
import time
from uldaq import get_daq_device_inventory, DaqDevice, InterfaceType, Range, AOutFlag

# === Config ===
AO_CHANNEL = 0                  # Analog output channel (typically 0)
SAMPLE_RATE = 1000              # Samples per second (software timed)
DURATION = 5                    # Duration in seconds
FREQ = 1.0                      # Frequency of the sine wave (Hz)
AMPLITUDE = 2.5                 # Peak amplitude (volts)
OFFSET = 2.5                    # DC offset to center sine wave (volts)
VOLTAGE_RANGE = Range.UNI5VOLTS
MIN_VOLTAGE = 0.0
MAX_VOLTAGE = 5.0

def main():
    # Discover connected DAQ devices
    devices = get_daq_device_inventory(InterfaceType.ANY)
    if not devices:
        raise RuntimeError("No DAQ devices found.")

    # Connect to the first available device
    daq_device = DaqDevice(devices[0])
    ao_device = daq_device.get_ao_device()
    ao_info = ao_device.get_info()

    if ao_device is None:
        raise RuntimeError("Selected device does not support analog output.")

    try:
        daq_device.connect()

        # Create sine wave data
        num_samples = int(SAMPLE_RATE * DURATION)
        t = np.linspace(0, DURATION, num_samples, endpoint=False)
        sine_wave = AMPLITUDE * np.sin(2 * np.pi * FREQ * t) + OFFSET

        print("Outputting sine wave...")

        for value in sine_wave:
            # Clip value to valid output range
            clipped_value = max(MIN_VOLTAGE, min(value, MAX_VOLTAGE))
            ao_device.a_out(AO_CHANNEL, VOLTAGE_RANGE, AOutFlag.DEFAULT, clipped_value)
            time.sleep(1.0 / SAMPLE_RATE)

        print("Done.")

    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        daq_device.disconnect()
        daq_device.release()

if __name__ == "__main__":
    main()
