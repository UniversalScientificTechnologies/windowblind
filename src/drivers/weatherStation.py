#!/usr/bin/env python
# -*- coding: utf-8 -*-

import math
import time
import rospy
import std_msgs
import actionlib
import json
from std_msgs.msg import String
from std_msgs.msg import Float32
from arom.srv import *
from arom.msg import *
import numpy as np
import serial
from astropy.time import Time
import astropy.units as u
import MySQLdb as mdb
import httplib2





def calc_dewpoint(temp, hum):
    x = 1 - 0.01 * hum;

    dewpoint = (14.55 + 0.114 * temp) * x;
    dewpoint = dewpoint + ((2.5 + 0.007 * temp) * x) ** 3;
    dewpoint = dewpoint + (15.9 + 0.117 * temp) * x ** 14;
    dewpoint = temp - dewpoint;

    return dewpoint


class weatherStation(object):
    def __init__(self, parent = None, arg = None, name = "weatherStation", port="", connect = True, var = {}):
        self.arg = arg
        self.Autoconnect = connect
        self.port = port
        self.parent = parent
        self.name = self.arg['name']
        self.sname = self.name
        self.variables = var
        
        ##
        ##  Pripojeni k databazi
        ##

        self.connection = mdb.connect(host="localhost", user="root", passwd="root", db="AROM", use_unicode=True, charset="utf8")
        self.cursorobj = self.connection.cursor()

        ##
        ##  Inicializace vlastniho ovladace
        ##

        self.init()

        s_RegisterDriver = rospy.Service('driver/weatherStation/%s' %self.name, arom.srv.DriverControl, self.reset)

        ##
        ##  Ceka to na spusteni AROMbrain nodu
        ##

        rospy.init_node('AROM_weatherStation')
        rospy.loginfo("%s: wait_for_service: 'arom/RegisterDriver'" % self.name)
        rospy.wait_for_service('arom/RegisterDriver')
        rospy.loginfo("%s: >> brain found" % self.name)

        ##
        ##  Registrace zarizeni
        ##  >Arom returns 1 - OK, 0 - False
        ##

        RegisterDriver = rospy.ServiceProxy('arom/RegisterDriver', arom.srv.RegisterDriver)
        registred = RegisterDriver(name = self.name, sname = self.name, driver = self.arg['driver'], device = self.arg['type'], service = 'arom/driver/%s/%s' %(self.arg['type'], self.name), status = 1)
        rospy.loginfo("%s: >> register %s driver: %s" %(self.name, 'AWS01A', registred))


        ##
        ##  Ovladac se pripoji k montazi
        ##

        if self.Autoconnect:
            self.connect()

        ##
        ##  Ovladac pujde ukoncit
        ##

        rate = rospy.Rate(0.1)
        while not rospy.is_shutdown():
            try:
                data = self.mesure()
                self.datalog(data)
            except Exception, e:
                rospy.logerr(e)
            rate.sleep()

        self.connection.close()


    def _sql(self, query, read=False):
        #print query
        result = None
        try:
            self.cursorobj.execute(query)
            result = self.cursorobj.fetchall()
            if not read:
                self.connection.commit()
        except Exception, e:
            rospy.logerr("MySQL: %s" %repr(e))
        return result


    def reset(self, val=None):
        pass

    def datalog(self, val = []):
        for row in val:
            #self._sql("INSERT INTO `AROM`.`weather` (`date`, `type_id`, `sensors_id`, `value`) VALUES ('%f', '%i', '%i', '%f');" % (row['time'], 0, 0, row['value']))
            self._sql("INSERT INTO `AROM`.`weather` (`date`, `type_id`, `sensors_id`, `value`) VALUES ('%f', %i, (SELECT sensors_id FROM sensors WHERE sensor_name = '%s'), '%f');" % (row['time'], 0, row['name'], row['value']))
        pass



###############################################################################################################################################################################
#################################################################################################################################################################################
#################################################################################################################################################################################
#################################################################################################################################################################################
#################################################################################################################################################################################

class weatherDataUploader(object):
    def __init__(self, parent = None, arg = None, name = "weatherDataUploader", var = {}):
        self.arg = arg
        self.name = self.arg['name']
        self.sname = self.name
        self.variables = var
        
        ##
        ##  Pripojeni k databazi
        ##

        self.connection = mdb.connect(host="localhost", user="root", passwd="root", db="AROM", use_unicode=True, charset="utf8")
        self.cursorobj = self.connection.cursor()

        ##
        ##  Inicializace vlastniho ovladace
        ##

        self.init()

        s_RegisterDriver = rospy.Service('driver/weatherStation/%s' %self.name, arom.srv.DriverControl, self.reset)

        ##
        ##  Ceka to na spusteni AROMbrain nodu
        ##

        rospy.init_node('AROM_weatherUploader')
        rospy.loginfo("%s: wait_for_service: 'arom/RegisterDriver'" % self.name)
        rospy.wait_for_service('arom/RegisterDriver')
        rospy.loginfo("%s: >> brain found" % self.name)

        ##
        ##  Registrace zarizeni
        ##  >Arom returns 1 - OK, 0 - False
        ##

        RegisterDriver = rospy.ServiceProxy('arom/RegisterDriver', arom.srv.RegisterDriver)
        registred = RegisterDriver(name = self.name, sname = self.name, driver = self.arg['driver'], device = self.arg['type'], service = 'arom/driver/%s/%s' %(self.arg['type'], self.name), status = 1)
        rospy.loginfo("%s: >> register %s driver: %s" %(self.name, 'AWS01A', registred))


        ##
        ##  Ovladac pujde ukoncit
        ##

        rate = rospy.Rate(0.1)
        while not rospy.is_shutdown():
            try:
                values = self._sql('SELECT ROUND(weather.date), weather.value, sensors.sensor_name, sensors.sensor_quantity_type, sensors.sensor_field_quantity_type, sensors.sensor_field_name FROM weather JOIN sensors ON weather.sensors_id = sensors.sensors_id WHERE weather.date > %f GROUP BY weather.sensors_id ORDER BY weather.date DESC;' %(Time.now().unix-30))
                data = self.datapush(values)
            except Exception, e:
                rospy.logerr(e)
            time.sleep(30)

        self.connection.close()

    def _sql(self, query, read=False):
        #print query
        result = None
        try:
            self.cursorobj.execute(query)
            result = self.cursorobj.fetchall()
            if not read:
                self.connection.commit()
        except Exception, e:
            rospy.logerr("MySQL: %s" %repr(e))
        return result

    def reset(self, val=None):
        pass

    def transform(self, value, inT, outT):
        if inT =='C':
            if outT == 'F':
                return value*1.8+32.00
            else:
                return value
        elif inT =='MS':
            if outT == 'MPS':
                return (value*2.2369362920544)
            else:
                return value
        else:
            return value


############################################################################################################################################################################
############################################################################################################################################################################
############################################################################################################################################################################
############################################################################################################################################################################
############################################################################################################################################################################

######################################################################################
######################################################################################
##                                                                                  ##
##                  Driver for --AWS01A-- MLAB weather station                      ##
##                 ============================================                     ##
##                                                                                  ##
##                                                                                  ##
######################################################################################
        
class AWS01B(weatherStation):
    def init(self): 
        self.variables = {
            'AWS_LTS_temp': 0,
            'AWS_SHT_temp': 0,
            'AWS_SHT_humi': 0
            }
        rospy.loginfo("AWS01A weather station requires 'pymlab_drive' service from 'ROSpymlabServer' node")
        rospy.loginfo("run>> 'rosrun arom initPymlab.py'")
        rospy.wait_for_service('pymlab_drive')
        self.pymlab = rospy.ServiceProxy('pymlab_drive', PymlabDrive)
        rospy.loginfo("%s: >> 'ROSpymlabServer' found" % self.name)
        self.last_wind_mes = Time.now()

        self.pymlab(device="AWS_light", method="config", parameters=str(0x0000))


    def mesure(self):
    # SHT31_out
        TempHumOut = eval(self.pymlab(device="AWS_humi", method="get_TempHum", parameters=None).value)

    # SHT31_in
        TempHumIn = eval(self.pymlab(device="AWS_humi_in", method="get_TempHum", parameters=None).value)

    # Light
        Light = eval(self.pymlab(device="AWS_light", method="get_lux", parameters=None).value)/10

    # WIND
        speed1 = abs(eval(self.pymlab(device="AWS_wind_s", method="get_speed", parameters='').value))
        speed2 = abs(eval(self.pymlab(device="AWS_wind_s", method="get_speed", parameters='').value))
        speed3 = abs(eval(self.pymlab(device="AWS_wind_s", method="get_speed", parameters='').value))
	speed = (speed1 + speed2 + speed3)/3
        speed = speed * 0.975 # kmph

	# plot '1472745590-log.txt' u 1:($2 * 0.3 * 3.25) w l,  '1472745590-log.txt' u 1:($3 * 3.6) w l lw 5

        
        rospy.loginfo('OUT: %s-C%%, %s-lux, %s-mps, IN: %s-C-%%' %(str(TempHumOut), str(Light), str(speed), str(TempHumIn)))

        data_time = time.time()
        return [#{'value':AWS_LTS_temp_ref, 'name':'AWS_telescope_temp_lts_ref', 'guantity': 'C', 'time': data_time},
                {'value':TempHumOut[0], 'name':'AWS_temp', 'guantity': 'C', 'time': data_time},
                {'value':TempHumOut[1], 'name':'AWS_humi', 'guantity': 'perc', 'time': data_time},
                {'value':TempHumIn[0], 'name':'IN_temp', 'guantity': 'C', 'time': data_time},
                {'value':TempHumIn[1], 'name':'IN_humi', 'guantity': 'perc', 'time': data_time},
                {'value':speed, 'name':'AWS_wind', 'guantity': 'ms-1', 'time': data_time},
                {'value':Light, 'name':'AWS_light', 'guantity': 'lux', 'time': data_time},
                {'value':calc_dewpoint(TempHumOut[0], TempHumOut[1]), 'name':'AWS_dewpoint', 'guantity': 'C', 'time': data_time},
                {'value':calc_dewpoint(TempHumIn[0], TempHumIn[1]), 'name':'IN_dewpoint', 'guantity': 'C', 'time': data_time}]

    def connect(self):
        pass


############################################################################################################################################################################
############################################################################################################################################################################
############################################################################################################################################################################
############################################################################################################################################################################
############################################################################################################################################################################

######################################################################################
######################################################################################
##                                                                                  ##
##                  Driver for --WEATHERCLOUD--                                     ##
##                 ============================================                     ##
##                                                                                  ##
##                                                                                  ##
######################################################################################
        
class WEATHERUNDERGROUND(weatherDataUploader):
    def init(self):
        pass

    def connect(se):
        pass

    def datapush(self, data):
        req = "?ID=%s&PASSWORD=%s&dateutc=now" %(self.arg['id'], self.arg['pass'])
        for row in data:
            #print row
            try:
                val = float(row[1])
                sourceType = row[3]
                outType = row[4]
            except Exception, e:
                print e

            req += "&"+row[5]+"="+str(self.transform(val, sourceType, outType))
        print "http://weatherstation.wunderground.com/weatherstation/updateweatherstation.php"+req
        resp, content = httplib2.Http().request("http://weatherstation.wunderground.com/weatherstation/updateweatherstation.php"+req)



if __name__ == '__main__':
    cfg = rospy.get_param("ObservatoryConfig/file")
    with open(cfg) as data_file:
        config = json.load(data_file)
    for x in config:
        if x['name'] == sys.argv[1]:
            break
    weatherStation = locals()[x['driver']](arg = x)
    #weatherStation = AWS01B()
