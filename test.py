from I2C_SLF3S_1300F import WaterCali
import csv
import time

water_cali = WaterCali()

# Test I2C connection
if water_cali.test_i2c():
    print("Ready to measure!")
    
    if water_cali.start_measure():
        print("Starting 1000Hz data collection for 10 seconds...")
        start_time = time.time()
        measurement_count = 0
        data_buffer = []  # Buffer to store all measurements
        
        try:
            while time.time() - start_time < 10.0:  # Run for 10 seconds
                measurement_start = time.time()
                
                # Read flow data
                result = water_cali.read_flow()
                if result:
                    flow, temp = result
                    timestamp_ms = int((time.time() - start_time) * 1000)
                    
                    # Buffer data instead of writing immediately
                    data_buffer.append({
                        'timestamp_ms': timestamp_ms,
                        'flow_rate_ml_min': flow,
                        'temperature_c': temp
                    })
                    
                    measurement_count += 1
                    
                    # Print progress every 1000 measurements (less frequent to avoid delays)
                    if measurement_count % 2000 == 0:
                        print(f"Measurements: {measurement_count}")
                
                # Calculate delay to maintain 1000Hz (1ms intervals)
                elapsed = time.time() - measurement_start
                delay = 0.001 - elapsed  # Target 1ms interval
                if delay > 0:
                    time.sleep(delay)
                    
        except KeyboardInterrupt:
            print("\nMeasurement interrupted by user")
        
        print(f"Data collection complete. Total measurements: {measurement_count}")
        print("Writing data to CSV file...")
        
        # Write all buffered data to CSV at once
        with open('flow_data.csv', 'w', newline='') as csvfile:
            fieldnames = ['timestamp_ms', 'flow_rate_ml_min', 'temperature_c']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data_buffer)
        
        print(f"Data saved to flow_data.csv")
        
        water_cali.stop_measure()
    else:
        print("Failed to start measurement")
else:
    print("I2C connection failed")

water_cali.close()