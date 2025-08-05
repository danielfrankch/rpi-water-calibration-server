from water_cali import WaterCali

water_cali = WaterCali()

# Test I2C connection
if water_cali.test_i2c():
    print("Ready to measure!")
    water_cali.start_measure()
    # ... take measurements ...
    water_cali.stop_measure()

water_cali.close()