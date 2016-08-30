#!/bin/bash

cd /home/odroid/

. /home/odroid/rosws/devel/setup.bash

sleep 5
screen -S bridge -d -m roslaunch rosbridge_server rosbridge_websocket.launch
rosparam load /home/odroid/rosws/src/windowblind/tools/parameters_blind.yaml
screen -S aromBrain -d -m rosrun arom aromBrain.py /home/odroid/rosws/src/arom/cfg/test.json
screen -S pymlab -d -m rosrun arom ROSpymlabServer.py

sleep 10
rosrun windowblind initPymlab.py
screen -S aws -d -m rosrun windowblind weatherStation.py aws
screen -S guard -d -m rosrun windowblind guard.py
screen -S controller -d -m rosrun windowblind controller.py

sleep 10
cd /home/odroid/rosws/src/windowblind/web
screen -S web -d -m python /home/odroid/rosws/src/windowblind/web/windowblind_web.py
