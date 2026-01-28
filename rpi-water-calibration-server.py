#!/usr/bin/env python3
"""
Water Calibration Server - ZMQ Interface
Provides a ZMQ req/reply server for water flow measurement and volume calculation.
"""

import zmq
import socket
import time
import re
import threading
from I2C_SLF3S_1300F import WaterCali

# Global variables
sample_frequency = 500  # Hz
vol_queue = None  # Stores volume in milliliters (mL)

def get_local_ip():
    """Get the local IP address of the machine"""
    try:
        # Connect to a dummy address to get local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "localhost"

def parse_measure_command(message):
    """
    Parse the water.measure command to extract duration
    
    Args:
        message (str): The incoming message
        
    Returns:
        float: Duration in seconds or None if parsing failed
    """
    # Match pattern: 'water.measure = duration'
    match = re.match(r'water\.measure\s*=\s*(\d+(?:\.\d+)?)', message.strip())
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None

def perform_water_measurement(duration):
    """
    Perform water flow measurement for the specified duration
    """
    global vol_queue
    
    water_cali = WaterCali()
    
    try:
        # Test I2C connection
        if not water_cali.test_i2c():
            return False, "error: I2C connection failed", None
        
        # Start measurement
        if not water_cali.start_measure():
            return False, "error: Failed to start measurement", None
        
        # Data collection
        start_time = time.time()
        measurement_count = 0
        flow_data = []
        next_measurement_time = start_time
        sample_interval = 1.0 / sample_frequency  # Time between samples in seconds
        
        print(f"Starting {duration}s measurement at {sample_frequency}Hz...")
        
        while time.time() - start_time < duration:
            current_time = time.time()
            
            # Only measure if we've reached the next scheduled time
            if current_time >= next_measurement_time:
                # Read flow data
                result = water_cali.read_flow()
                if result is not None:
                    flow_ml_min = result
                    timestamp = current_time - start_time
                    flow_data.append((timestamp, flow_ml_min))
                    measurement_count += 1
                    next_measurement_time += sample_interval
                else:
                    print("Warning: Failed to read flow data")
            else:
                # Small sleep to prevent busy waiting
                time.sleep(0.0001)
        
        # Stop measurement
        water_cali.stop_measure()
        
        # Calculate total volume
        if len(flow_data) < 2:
            return False, "error: Insufficient data collected", None
        
        # Integrate flow rate to get total volume
        total_volume_ml = 0.0
        for i in range(1, len(flow_data)):
            # Get time difference in minutes
            dt_min = (flow_data[i][0] - flow_data[i-1][0]) / 60.0
            # Average flow rate between two points (mL/min)
            avg_flow = (flow_data[i][1] + flow_data[i-1][1]) / 2.0
            # Volume increment in mL
            dv_ml = avg_flow * dt_min
            total_volume_ml += dv_ml
        
        # Store in global queue
        vol_queue = total_volume_ml
        
        print(f"Measurement complete: {measurement_count} samples, "
              f"Total volume: {total_volume_ml:.2f} mL")
        
        return True, total_volume_ml
        
    except Exception as e:
        return False, f"error: {str(e)}"
    finally:
        water_cali.close()

def handle_message(message):
    """
    Handle incoming ZMQ messages
    
    Args:
        message (str): The incoming message string
        
    Returns:
        str: Response message
    """
    global vol_queue
    
    message = message.strip()
    
    # Case 1: water.measure = duration
    if message.startswith('water.measure'):
        duration = parse_measure_command(message)
        if duration is None:
            return "error: Invalid measure command format"
        
        if duration <= 0:
            return "error: Duration must be positive"
        
        # Perform measurement in a separate thread to avoid blocking
        success, volume = perform_water_measurement(duration)
        if success:
            return volume
        else:
            print(f"Measurement failed: {volume}")
            return volume
            
    
    else:
        return "error: Unknown command"

def start_server():
    """Start the ZMQ req/reply server"""
    # Get local IP address
    local_ip = get_local_ip()
    port = 3200
    
    # Set up ZMQ context and socket
    context = zmq.Context()
    socket_zmq = context.socket(zmq.REP)
    
    try:
        # Bind to the local IP and port
        bind_address = f"tcp://{local_ip}:{port}"
        socket_zmq.bind(bind_address)
        print(f"Water calibration server listening on {bind_address}")
        
        while True:
            try:
                # Wait for next request from client
                message = socket_zmq.recv_string(zmq.NOBLOCK)
                print(f"Received request: {message}")
                
                # Process the message
                response = handle_message(message)
                print(f"Sending response: {response}")
                
                # Send reply back to client
                socket_zmq.send_string(str(response))
                
            except zmq.Again:
                # No message available, continue polling
                try:
                    time.sleep(0.001)
                except KeyboardInterrupt:
                    print("\nShutting down server...")
                    break
                continue
            except Exception as e:
                print(f"Error handling request: {e}")
                try:
                    socket_zmq.send_string(f"error: {str(e)}")
                except:
                    pass
    
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"Failed to start server: {e}")
    
    finally:
        socket_zmq.close()
        context.term()
        print("Server stopped")

if __name__ == "__main__":
    start_server()
