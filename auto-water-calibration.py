import octagonclient
from datetime import datetime
import os
import time
import random
import zmq
import csv
import configparser

def default_handler(address, *args):
    print(f"DEFAULT {address}: {args}")

def incoming_message_parser(message):
    print(message[1:])


ip = "127.0.0.1"
request_port = 4002


def deliverWater(oct, wallid, pokeid, duration, num_times, pause_duration):

    oct.calibrate(wallid=wallid, pokeid=pokeid, duration=duration)

    for x in range(num_times):
        oct.triggervalve(wallid=wallid, pokeid=pokeid)
        time.sleep(pause_duration)


VALVE_DURATIONS = [0.01, 0.015, 0.017, 0.02, 0.023, 0.025, 0.03, 0.035]
# VALVE_DURATIONS = [0.025]
wallids = [1,2,3,4,5,6,7,8]
pokeids = [0,1]


wallid = 0
pokeid = 0
valve = 0
pause_duration = 0.1

# Read ZMQ URL from config
config = configparser.ConfigParser()
config.read(os.path.expanduser('~/.dbconf'))
zmq_url = config['water']['url']

# Setup ZMQ connection
context = zmq.Context()
zmq_socket = context.socket(zmq.REQ)
zmq_socket.connect(zmq_url)

# Setup CSV file
now = datetime.now().strftime("%Y%m%d_%H%M%S")
csv_filename = f"Auto_Calibration_{now}.csv"
csv_file = open(csv_filename, 'w', newline='')
csv_writer = csv.writer(csv_file)
csv_writer.writerow(['rigid', 'valve', 'duration', 'volume', 'drops'])

try:
    oct = octagonclient.OctagonClient()

    print("Start Calibration")
    oct.startnewsession(f"..\..\Data\Calibration_{now}")
    time.sleep(0.1)
    for wallid in wallids:
        for pokeid in pokeids:
            valve += 1
            for dur in VALVE_DURATIONS:
                if dur < 0.05:
                    num_times = 100
                else:
                    num_times = 50
                    
                # Calculate total duration and send ZMQ request
                total_duration = num_times * (dur + pause_duration) + 2
                zmq_socket.send_string(f"water.measure = {total_duration}")
                
                # Wait 1s then deliver water
                time.sleep(1)
                deliverWater(oct, wallid, pokeid, dur, num_times, pause_duration)

                # Wait 2s then read ZMQ reply
                time.sleep(2)
                msg = zmq_socket.recv_string()
                if msg.startswith("error"):
                    raise RuntimeError(msg)
                
                volume_ml = float(msg)

                vol = volume_ml / num_times
                
                # Write to CSV
                csv_writer.writerow([464003, valve, dur, vol, 1])
                csv_file.flush()

    oct.stopsession()

finally:
    csv_file.close()
    zmq_socket.close()
    context.term()