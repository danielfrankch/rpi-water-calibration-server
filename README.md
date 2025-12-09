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
3. Configure RPi I2C bus:
```bash
sudo nano //boot/firmware/config.txt
```
Add the following lines:
```
dtparam=i2c_arm=on
dtparam=i2c_arm_baudrate=100000
```
Then CTRL + O, Enter
then ```sudo reboot```


