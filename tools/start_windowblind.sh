#!/bin/bash
LOG_FILE=/home/odroid/autostart.txt

echo "${PWD##*/}" >> ${LOG_FILE}

#export ROS_ROOT=/opt/ros/jade/share/ros
#export ROS_PACKAGE_PATH=/home/odroid/robozor/src:/opt/ros/jade/share:/opt/ros/jade/stacks
#export ROS_DISTRO=jade
#export ROS_ETC_DIR=/opt/ros/jade/etc/ros
#export ROSLISP_PACKAGE_DIRECTORIES=/home/odroid/robozor/devel/share/common-lisp
#export ROS_MASTER_URI=http://localhost:11311

#echo "#############################################" >> ${LOG_FILE}
#echo "Running autostart_screens.sh" >> ${LOG_FILE}
#echo $(date) >> ${LOG_FILE}
#echo "#############################################" >> ${LOG_FILE}


cd /home/odroid/
#echo "${PWD##*/}" >> ${LOG_FILE}

#. /robozor/devel/setup.bash
. /home/odroid/ros_ws/devel/setup.bash
#sleep 3
#screen -S core -d -m roscore

sleep 5
screen -S bridge -d -m roslaunch rosbridge_server rosbridge_websocket.launch
rosparam load /home/odroid/ros_ws/parameters.yaml
screen -S aromBrain -d -m rosrun arom aromBrain.py /home/odroid/ros_ws/src/arom/cfg/test.json 
screen -S pymlab -d -m rosrun arom ROSpymlabServer.py

sleep 10
rosrun windowblind initPymlab.py
screen -S aws -d -m rosrun windowblind weatherStation.py aws
screen -S guard -d -m rosrun windowblind guard.py
screen -S controller -d -m rosrun windowblind controller.py

sleep 10
cd /home/odroid/ros_ws/src/windowblind/web
screen -S web -d -m python /home/odroid/ros_ws/src/windowblind/web/windowblind_web.py
