#!/bin/sh
killall -9 roscore
killall -9 rosmaster
echo "===================" >> /home/odroid/test.txt
now=$(date +"%T")
echo "$now" >> /home/odroid/test.txt
echo $HOME >> /home/odroid/test.txt
#echo $ROS_PACKAGE_PATH >> /home/odroid/test.txt
/home/odroid/robozor/devel/setup.sh
echo $ROS_PACKAGE_PATH >> /home/odroid/test.txt
roscore &
sleep 5


roslaunch rosbridge_server rosbridge_websocket.launch &
rosparam load /home/odroid/robozor/parameters.yaml
rosrun arom aromBrain.py /home/odroid/robozor/src/arom/cfg/test.json &
rosrun arom ROSpymlabServer.py &

sleep 5
rosrun windowblind initPymlab.py &
rosrun windowblind weatherStation.py aws &
rosrun windowblind windowblind.py guard &
rosrun windowblind windowblind.py controller &

sleep 5
python /home/odroid/robozor/src/windowblind/web/windowblind_web.py &
#cd /home/odroid/robozor/src/windowblind/web
#python windowblind_web.py &
