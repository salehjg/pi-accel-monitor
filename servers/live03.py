from mpu6050 import mpu6050
from time import sleep          
from datetime import datetime, timedelta
import random
import threading
import numpy as np
import pickle
import bokeh
from bokeh.models import ColumnDataSource, DatetimeTickFormatter
from bokeh.io import curdoc
from bokeh.plotting import figure

data_accel = []
data_gyro = []
data_time = []
data_temp = []
lock = threading.Lock()
last_index = 0

sensor = mpu6050(0x68)

def get_data():
    accel_data = sensor.get_accel_data()
    gyro_data = sensor.get_gyro_data()
    temp = sensor.get_temp()
    return {"accel":[accel_data["x"], accel_data["y"], accel_data["z"]], "gyro":[gyro_data["x"], gyro_data["y"], gyro_data["z"]], "time":datetime.now(), "temp": temp}

def sensor_thread(name):
    while True:
        data_dict = get_data()
        with lock:
            data_accel.append(data_dict["accel"])
            data_gyro.append(data_dict["gyro"])
            data_time.append(data_dict["time"])
            #data_temp.append(data_dict["temp"])
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
                "data_accel_ms2": src_np[pair[0]:pair[1],:],
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
                last_index=0
        sleep(1)
        
t1 = threading.Thread(target=sensor_thread, args=(1,))
#t2 = threading.Thread(target=dump_thread, args=(2,))
t1.start()
#t2.start()

data_source = ColumnDataSource(data = {"Accel": [], "DateTime": []}) ## Data Source

fig = figure(x_axis_type="datetime", tooltips=[("Accel", "@Accel")], title = "Acceleration (m/S^2)", sizing_mode='stretch_both')
fig.line(x="DateTime", y="Accel", line_color="tomato", line_width=3.0, source=data_source,)
fig.xaxis.axis_label="Date"
fig.yaxis.axis_label="Mean Acceleration - 9.8/3 (m/S^2)"
fig.xaxis.formatter=DatetimeTickFormatter( seconds = '%Y_%m_%D_%H_%M_%S')
fig.xaxis.major_label_orientation = 0.785 # pi/4

def update_chart():
    global data_source 
    global last_index
    with lock:
        abs_accel = np.mean(np.array(data_accel[last_index+1:]), axis=-1) - 9.8/3.0
        new_row = {"Accel":abs_accel , "DateTime":data_time[last_index+1:]}
        data_source.stream(new_row)
        last_index = len(data_accel) - 1

curdoc().add_periodic_callback(update_chart, 1000)
curdoc().add_root(fig)
