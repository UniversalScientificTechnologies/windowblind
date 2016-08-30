#!/usr/bin/env python

import sys
import pymlab
import rospy
import time
from pymlab import config
from std_msgs.msg import String
from arom.srv import *
from arom.msg import *



if __name__ == "__main__":
    i2c = str({
                "device": "smbus",
                "port": 1
    })
    bus = str([
                {
                    "name":           "AWS_humi_in",
                    "type":           "sht31",
                    "address":        0x45
                },
                {
                    "name":           "AWS_humi",
                    "type":           "sht31",
                    "address":        0x44
                },
                {
                    "name":           "AWS_wind_s",
                    "type":           "rps01"
                },
                {
                    "name":          "AWS_light",
                    "type":          "isl03"
                },
                {
                    "name":           "blind",
                    "type":           "TCA6416A"
                    #"type":           "I2CIO_TCA9535", "address":        0x27,
                }       
    ])

    rospy.wait_for_service('pymlab_init')

    msg_pymlab = rospy.Publisher('pymlab_server', PymlabServerStatusM, queue_size=10)
    rospy.init_node('pymlab_client', anonymous=True)

    pymlab = rospy.ServiceProxy('pymlab_init', PymlabInit)
    print pymlab(i2c=i2c, bus=bus)
    
    msg_pymlab.publish(name = "", data="{'rate': 0.01, 'start': True, 'AutoInputs': {}}")
