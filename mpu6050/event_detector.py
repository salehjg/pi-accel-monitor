import smbus					#import SMBus module of I2C
from time import sleep          #import
from datetime import datetime, timedelta
import random
import threading
import numpy as np
import pickle



#some MPU6050 Registers and their Address
PWR_MGMT_1   = 0x6B
SMPLRT_DIV   = 0x19
CONFIG       = 0x1A
GYRO_CONFIG  = 0x1B
INT_ENABLE   = 0x38
ACCEL_XOUT_H = 0x3B
ACCEL_YOUT_H = 0x3D
ACCEL_ZOUT_H = 0x3F
GYRO_XOUT_H  = 0x43
GYRO_YOUT_H  = 0x45
GYRO_ZOUT_H  = 0x47

bus = smbus.SMBus(1) 	# or bus = smbus.SMBus(0) for older version boards
Device_Address = 0x68   # MPU6050 device address

data_accel = []
data_gyro = []
data_time = []
lock = threading.Lock()

sample_size = 100


def MPU_Init():
    #write to sample rate register
    bus.write_byte_data(Device_Address, SMPLRT_DIV, 7)
    
    #Write to power management register
    bus.write_byte_data(Device_Address, PWR_MGMT_1, 1)
    
    #Write to Configuration register
    bus.write_byte_data(Device_Address, CONFIG, 0)
    
    #Write to Gyro configuration register
    bus.write_byte_data(Device_Address, GYRO_CONFIG, 24)
    
    #Write to interrupt enable register
    bus.write_byte_data(Device_Address, INT_ENABLE, 1)

def read_raw_data(addr):
    #Accelero and Gyro value are 16-bit
        high = bus.read_byte_data(Device_Address, addr)
        low = bus.read_byte_data(Device_Address, addr+1)
    
        #concatenate higher and lower value
        value = ((high << 8) | low)
        
        #to get signed value from mpu6050
        if(value > 32768):
                value = value - 65536
        return value


def get_data():
    #Read Accelerometer raw value
    acc_x = read_raw_data(ACCEL_XOUT_H)
    acc_y = read_raw_data(ACCEL_YOUT_H)
    acc_z = read_raw_data(ACCEL_ZOUT_H)
    
    #Read Gyroscope raw value
    gyro_x = read_raw_data(GYRO_XOUT_H)
    gyro_y = read_raw_data(GYRO_YOUT_H)
    gyro_z = read_raw_data(GYRO_ZOUT_H)
    
    #Full scale range +/- 250 degree/C as per sensitivity scale factor
    Ax = acc_x/16384.0
    Ay = acc_y/16384.0
    Az = acc_z/16384.0
    
    Gx = gyro_x/131.0
    Gy = gyro_y/131.0
    Gz = gyro_z/131.0
    
    return {"accel":[Ax*1000.0, Ay*1000.0, Az*1000.0], "gyro":[Gx, Gy, Gz], "time":datetime.now()}#.strftime("%Y_%m_%D_%H_%M_%S")}

def sensor_thread(name):
    while True:
        data_dict = get_data()
        with lock:
            data_accel.append(data_dict["accel"])
            data_gyro.append(data_dict["gyro"])
            data_time.append(data_dict["time"])
        sleep(250.0 * 10**(-6)) # 250uSec

def process_accel(src:list, src_times:list, threshold=30.0, merge_less_than_sec=5):
    src_np = np.array(src, dtype=np.float32)
    mean = np.mean(src_np, axis=0)
    l = len(src)
    mask = np.sqrt(np.power(src_np-mean, 2.0)) > threshold # nx3 bool
    mask = np.array(mask, dtype=np.float32) # nx3 float
    mask = np.sum(mask, axis=1) # nx1 
    mask = mask >= 1
    
    found = []
    status = False
    start = -1 
    for i in range(l):
        if not status:
            if mask[i]:
                status = True
                start = i
        else:
            if (not mask[i]) or i == (l-1):
                status = False
                found.append([start, i])
     
    l = len(found) 
    to_be_removed = []
    for i in range(l-1):
        crnt_stop_time = src_times[found[i][1]]
        next_start_time = src_times[found[i+1][0]]
        if next_start_time - crnt_stop_time < timedelta(seconds=merge_less_than_sec):
            found[i+1][0] = found[i][0]
            to_be_removed.append(i)

    to_be_removed_sorted = sorted(to_be_removed, key=int, reverse=True)
    for i in to_be_removed_sorted:
        del found[i]

    events = []
    for pair in found:
        total_sec = (src_times[pair[1]]-src_times[pair[0]]).total_seconds()
        print("Found event at " + str(src_times[pair[0]]) + " for " + str(total_sec) + " seconds." )
        events.append(
            {
                "start": src_times[pair[0]],
                "stop": src_times[pair[1]],
                "total_sec": total_sec,
                "data_accel_mg": src_np[pair[0]:pair[1],:],
                "data_time": src_time[pair[0]:pair[1]]
            }
        )

    return events

def dump_events(events:list, fname=datetime.now()):
    with open(fname.strftime("%Y_%m_%d.%H_%M_%S")+".pickle", "wb") as f:
        pickle.dump(events, f)

def dump_thread(name):
    while True:
        if len(data_time) > 10**4:
            with lock:
                events_list = process_accel(data_accel, data_time)
                dump_events(events_list)
                data_accel.clear()
                data_time.clear()
                data_gyro.clear()
        sleep(1)

MPU_Init()
t1 = threading.Thread(target=sensor_thread, args=(1,))
t2 = threading.Thread(target=dump_thread, args=(2,))
t1.start()
t2.start()

