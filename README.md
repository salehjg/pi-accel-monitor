# pi-accel-monitor
Raspberry PI Based Accelerometer Monitoring Server 

# Requirements
```bash
sudo apt install libatlas-base-dev
sudo pip3 install bokeh mpu6050-raspberrypi
```

Also make sure `I2C` and `SSH` are enabled in `raspiconfig`.

We use 3.3v `MPU6050` as the `I2C` accel/gyro chip. It could be directly connected to the `I2C` pins of any RPI.

# Running A `bokeh` Server
Use the bash script:
```bash
sh run_server.sh servers/live03.py
```
 
