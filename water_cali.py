"""
WaterCali - Water Flow Calibration System for SLF3S-1300F Flow Meter
Designed for Raspberry Pi 4B with native I2C interface
"""

import time
import logging
from typing import Optional, Tuple

try:
    import smbus2
except ImportError:
    print("Warning: smbus2 not installed. Install with: pip install smbus2")
    smbus2 = None


class WaterCali:
    """
    Water calibration class for SLF3S-1300F flow meter via Raspberry Pi native I2C interface.
    
    The SLF3S-1300F is a liquid flow sensor that communicates via I2C protocol.
    Default I2C address is 0x08.
    """
    
    # SLF3S-1300F I2C address (7-bit address)
    FLOW_METER_ADDRESS = 0x08
    
    # Command codes for SLF3S-1300F
    CMD_START_CONTINUOUS_MEASUREMENT = [0x36, 0x08]
    CMD_STOP_CONTINUOUS_MEASUREMENT = [0x3F, 0xF9]
    CMD_READ_MEASUREMENT = [0xE1, 0x02]
    CMD_SOFT_RESET = [0x00, 0x06]
    CMD_READ_PRODUCT_ID = [0xE1, 0x02]
    
    def __init__(self, i2c_bus: int = 1):
        """
        Initialize the WaterCali class.
        
        Args:
            i2c_bus (int): I2C bus number (default: 1 for Raspberry Pi)
        """
        self.i2c_bus = i2c_bus
        self.bus = None
        self.measuring = False
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        if smbus2 is None:
            self.logger.error("smbus2 library not available. Please install it.")
            return
            
        try:
            self.bus = smbus2.SMBus(self.i2c_bus)
            self.logger.info(f"I2C bus {self.i2c_bus} initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize I2C bus {self.i2c_bus}: {e}")
    
    def test_i2c(self) -> bool:
        """
        Test I2C connection with the flow meter.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        if self.bus is None:
            print("I2C connection to flow meter failed - bus not initialized")
            return False
            
        try:
            # Try to read from the device to test connection
            # We'll attempt a soft reset command which should be acknowledged
            self.bus.write_i2c_block_data(
                self.FLOW_METER_ADDRESS, 
                self.CMD_SOFT_RESET[0], 
                [self.CMD_SOFT_RESET[1]]
            )
            
            # Small delay after reset
            time.sleep(0.1)
            
            # If we get here without exception, connection is working
            print("I2C connection to flow meter successful")
            self.logger.info("SLF3S-1300F flow meter detected and responding")
            return True
            
        except OSError as e:
            if e.errno == 121:  # Remote I/O error - device not found
                print("I2C connection to flow meter failed - device not found")
                self.logger.error("SLF3S-1300F not found on I2C bus")
            else:
                print(f"I2C connection to flow meter failed - {e}")
                self.logger.error(f"I2C communication error: {e}")
            return False
        except Exception as e:
            print(f"I2C connection to flow meter failed - {e}")
            self.logger.error(f"Unexpected error during I2C test: {e}")
            return False
    
    def start_measure(self) -> bool:
        """
        Start continuous flow measurement on the SLF3S-1300F.
        
        Returns:
            bool: True if measurement started successfully, False otherwise
        """
        if self.bus is None:
            self.logger.error("Cannot start measurement - I2C bus not initialized")
            return False
            
        if self.measuring:
            self.logger.warning("Measurement already in progress")
            return True
            
        try:
            # Send start continuous measurement command
            self.bus.write_i2c_block_data(
                self.FLOW_METER_ADDRESS,
                self.CMD_START_CONTINUOUS_MEASUREMENT[0],
                [self.CMD_START_CONTINUOUS_MEASUREMENT[1]]
            )
            
            # Wait a bit for the sensor to start
            time.sleep(0.05)
            
            self.measuring = True
            self.logger.info("Started continuous flow measurement")
            print("Flow measurement started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start measurement: {e}")
            print(f"Failed to start flow measurement: {e}")
            return False
    
    def stop_measure(self) -> bool:
        """
        Stop continuous flow measurement on the SLF3S-1300F.
        
        Returns:
            bool: True if measurement stopped successfully, False otherwise
        """
        if self.bus is None:
            self.logger.error("Cannot stop measurement - I2C bus not initialized")
            return False
            
        if not self.measuring:
            self.logger.warning("No measurement in progress")
            return True
            
        try:
            # Send stop continuous measurement command
            self.bus.write_i2c_block_data(
                self.FLOW_METER_ADDRESS,
                self.CMD_STOP_CONTINUOUS_MEASUREMENT[0],
                [self.CMD_STOP_CONTINUOUS_MEASUREMENT[1]]
            )
            
            # Wait a bit for the sensor to stop
            time.sleep(0.05)
            
            self.measuring = False
            self.logger.info("Stopped continuous flow measurement")
            print("Flow measurement stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop measurement: {e}")
            print(f"Failed to stop flow measurement: {e}")
            return False
    
    def read_flow(self) -> Optional[Tuple[float, float]]:
        """
        Read flow and temperature values from the sensor.
        Must be called after start_measure().
        
        Returns:
            Tuple[float, float]: (flow_rate_ml_min, temperature_celsius) or None if error
        """
        if self.bus is None:
            self.logger.error("Cannot read flow - I2C bus not initialized")
            return None
            
        if not self.measuring:
            self.logger.error("Cannot read flow - measurement not started")
            return None
            
        try:
            # Read 9 bytes: 2 bytes flow + 1 CRC + 2 bytes temp + 1 CRC + 2 bytes aux + 1 CRC
            data = self.bus.read_i2c_block_data(self.FLOW_METER_ADDRESS, 0x00, 9)
            
            # Extract flow data (first 2 bytes)
            flow_raw = (data[0] << 8) | data[1]
            # Convert to signed 16-bit
            if flow_raw > 32767:
                flow_raw -= 65536
                
            # Extract temperature data (bytes 3-4)
            temp_raw = (data[3] << 8) | data[4]
            # Convert to signed 16-bit
            if temp_raw > 32767:
                temp_raw -= 65536
            
            # Convert to physical units based on datasheet
            # Flow: scaling factor and offset depend on calibration
            flow_ml_min = flow_raw / 120.0  # Approximate scaling for SLF3S-1300F
            
            # Temperature: scaling factor from datasheet
            temp_celsius = temp_raw / 200.0
            
            return (flow_ml_min, temp_celsius)
            
        except Exception as e:
            self.logger.error(f"Failed to read flow data: {e}")
            return None
    
    def close(self):
        """
        Clean up resources and close I2C connection.
        """
        if self.measuring:
            self.stop_measure()
            
        if self.bus is not None:
            self.bus.close()
            self.logger.info("I2C bus closed")


def main():
    """
    Example usage of the WaterCali class.
    """
    # Create instance
    water_cali = WaterCali()
    
    # Test I2C connection
    if water_cali.test_i2c():
        print("Flow meter connected successfully!")
        
        # Start measurement
        if water_cali.start_measure():
            try:
                # Read some measurements
                for i in range(5):
                    time.sleep(1)
                    result = water_cali.read_flow()
                    if result:
                        flow, temp = result
                        print(f"Flow: {flow:.2f} ml/min, Temperature: {temp:.1f}°C")
                    else:
                        print("Failed to read flow data")
            finally:
                # Stop measurement
                water_cali.stop_measure()
    else:
        print("Failed to connect to flow meter")
    
    # Clean up
    water_cali.close()


if __name__ == "__main__":
    main()
