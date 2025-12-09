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
        next_measurement_time = start_time
        
        try:
            while time.time() - start_time < 10.0:  # Run for 10 seconds
                current_time = time.time()
                
                # Only measure if we've reached the next scheduled time
                if current_time >= next_measurement_time:
                    # Read flow data
                    result = water_cali.read_flow()
                    if result:
                        flow = result
                        timestamp_ms = int((current_time - start_time) * 1000)
                        
                        # Buffer data instead of writing immediately
                        data_buffer.append([timestamp_ms, flow])  # Use list for speed
                        
                        measurement_count += 1
                        next_measurement_time += 0.002  # Schedule next measurement in 1ms (1000Hz)
                
                # Small sleep to prevent busy waiting and allow other processes
                else:
                    time.sleep(0.0001)  # 0.1ms sleep when not measuring
                    
        except KeyboardInterrupt:
            print("\nMeasurement interrupted by user")
        
        print(f"Data collection complete. Total measurements: {measurement_count}")
        print(f"Actual sampling rate: {measurement_count/10.0:.1f} Hz")
        print("Writing data to CSV file...")
        
        # Write all buffered data to CSV at once
        with open('flow_data.csv', 'w', newline='') as csvfile:
            fieldnames = ['timestamp_ms', 'flow_rate_ml_min']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            # Convert list data back to dict format for CSV writing
            for data_point in data_buffer:
                writer.writerow({
                    'timestamp_ms': data_point[0],
                    'flow_rate_ml_min': data_point[1],
                })
        
        print(f"Data saved to flow_data.csv")
        
        water_cali.stop_measure()
    else:
        print("Failed to start measurement")
else:
    print("I2C connection failed")

water_cali.close()