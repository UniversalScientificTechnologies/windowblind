#!/bin/sh

/home/odroid/robozor/devel/setup.bash
.robozor/devel/setup.bash
echo "01" >> /home/odroid/test
export ROS_PACKAGE_PATH='/opt/ros/jade/share:/opt/ros/jade/stacks:/home/odroid/robozor/src'
source /opt/ros/jade/setup.bash
source /home/odroid/robozor/devel/setup.bash

echo "02" >> /home/odroid/test
roscore &

echo "03" >> /home/odroid/test
sleep 5
echo "04" >> /home/odroid/test

roslaunch rosbridge_server rosbridge_websocket.launch &
echo "05" >> /home/odroid/test
rosparam load /home/odroid/robozor/parameters.yaml &
echo "06" >> /home/odroid/test

#rosrun arom aromBrain.py /home/odroid/robozor/src/arom/cfg/test.json &
#rosrun arom ROSpymlabServer.py &
#
#sleep 5
#rosrun windowblind initPymlab.py
#rosrun windowblind weatherStation.py aws &
#rosrun windowblind windowblind.py guard &
#rosrun windowblind windowblind.py controller &
#
#sleep 5
#cd /home/odroid/robozor/src/windowblind/web
#python windowblind_web.py &
