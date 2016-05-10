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
                "device": "hid",
                "port": 1,
    })
    bus = str([
                {
                    "name":           "AWS_humi",
                    "type":           "sht31"
                },{
                    "name":           "AWS_wind_s",
                    "type":           "rps01"
                },{
                    "name":           "AWS_temp_ref",
                    "type":           "lts01"
                },{
                    "name":           "AWS_wind_d",
                    "type":           "mag01",
                    "gauss":          0.88,
                },{
                    "name":           "StatusLCD",
                    "type":           "i2clcd"
                },#{
                #    "name":           "AWS_humi_in",
                #    "type":           "sht25"
                #}#,{
                #    "name":           "dd_temp_g0a",
                #    "type":           "sht25"
                #}
                #,{
                #    "name":           "dd_heater_g0a",
                #    "type":           "i2cpwm",
                #},
                {
                    "name":           "gpio",
                    "type":           "i2cio",
                }
                
    ])
    i2c2 = str({
            "device": "smbus",
            "port": 1,
        })
    bus2 = str([
                {
                    "name":           "dd_temp_g0a",
                    "type":           "sht25"

                }#{
                #    "name":           "io",
                #    "type":           "i2cio",
                #},
                
            ])




    msg_pymlab = rospy.Publisher('pymlab_server', PymlabServerStatusM, queue_size=10)
    rospy.init_node('pymlab_client', anonymous=True)

    pymlab = rospy.ServiceProxy('pymlab_init', PymlabInit)
    print pymlab(i2c=i2c, bus=bus)
    print pymlab(i2c=i2c2, bus=bus2)
    
    msg_pymlab.publish(name = "", data="{'rate': 0.01, 'start': True, 'AutoInputs': {}}")
