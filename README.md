# Raspberry Pi Water Calibration Server

This project provides a Python interface for the SLF3S-1300F flow meter connected to a Raspberry Pi 4B via USB-I2C dongle.

## Hardware Setup

- Raspberry Pi 4B
- USB-I2C dongle (connected to USB port)
- SLF3S-1300F flow meter (connected to I2C bus of the dongle)

## Installation

1. Install required Python packages:
```bash
pip install -r requirements.txt
```

2. Ensure I2C is enabled on your Raspberry Pi:
```bash
sudo raspi-config
# Navigate to Interfacing Options > I2C > Enable
```

## Usage

```python
from water_cali import WaterCali

# Create instance
water_cali = WaterCali()

# Test I2C connection
if water_cali.test_i2c():
    # Start measurement
    water_cali.start_measure()
    
    # Read flow data
    flow_data = water_cali.read_flow()
    if flow_data:
        flow, temp = flow_data
        print(f"Flow: {flow:.2f} ml/min, Temperature: {temp:.1f}°C")
    
    # Stop measurement
    water_cali.stop_measure()

# Clean up
water_cali.close()
```

## WaterCali Class Methods

- `test_i2c()`: Test I2C connection with the flow meter
- `start_measure()`: Start continuous flow measurement
- `stop_measure()`: Stop continuous flow measurement
- `read_flow()`: Read current flow rate and temperature
- `close()`: Clean up resources

## Flow Meter Details

The SLF3S-1300F is a liquid flow sensor with the following specifications:
- I2C address: 0x08
- Flow range: 0-40 ml/min
- Temperature measurement included
- I2C communication protocol

## Troubleshooting

1. **"I2C connection to flow meter failed"**: 
   - Check physical connections
   - Verify I2C address (default: 0x08)
   - Ensure USB-I2C dongle is properly recognized

2. **Import errors**:
   - Install smbus2: `pip install smbus2`
   - Ensure you're running on a system with I2C support
