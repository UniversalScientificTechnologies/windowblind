#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import time
import rospy
import actionlib
import json
import std_msgs
from std_msgs.msg import String
from std_msgs.msg import Float32
import windowblind
import arom
from arom.srv import *
#from windowblind.msg import *
from astropy.time import Time
import astropy.units as u
import time
import MySQLdb as mdb
import httplib2


############################################################################################################################################################################
############################################################################################################################################################################
######################                                                         #############################################################################################
######################                          WINDOW                         #############################################################################################
######################                                                         #############################################################################################
############################################################################################################################################################################
############################################################################################################################################################################

class window(object):
    def __init__(self, arg = None, name = "window", var = {}, config = {}):
        self.arg = arg
        self.name = self.arg['name']
        self.sname = self.name
        self.variables = var
        self.globalvariables = config
        
        ##
        ##  Pripojeni k databazi
        ##

        self.connection = mdb.connect(host="localhost", user="root", passwd="root", db="AROM", use_unicode=True, charset="utf8")
        self.cursorobj = self.connection.cursor()

        ##
        ##  Inicializace vlastniho ovladace
        ##

        self.init()

        ##
        ##  Inicializace vlastniho ovladace
        ##


        s_RegisterDriver = rospy.Service('driver/window/%s' %(self.name), DriverControl, self.serviceHandler)

        ##
        ##  Ceka to na spusteni AROMbrain nodu
        ##

        rospy.init_node(self.arg['name'])
        rospy.loginfo("%s: wait_for_service: 'arom/RegisterDriver'" % self.name)
        rospy.wait_for_service('arom/RegisterDriver')
        rospy.loginfo("%s: >> brain found" % self.name)

        ##
        ##  Registrace zarizeni
        ##  >>> Arom returns 1 - OK, 0 - False
        ##

        RegisterDriver = rospy.ServiceProxy('arom/RegisterDriver', arom.srv.RegisterDriver)
        registred = RegisterDriver(name = self.arg['name'], sname = self.arg['name'], driver = self.arg['driver'], device = self.arg['type'], service = 'arom/driver/%s/%s' %(self.arg['type'], self.arg['name']), status = 1)
        rospy.loginfo("'%s': >> register '%s' driver: '%s'" %(self.arg['name'], 'window', registred))


        ##
        ##  Ovladac pujde ukoncit
        ##
        rate = rospy.Rate(10)
        while not rospy.is_shutdown():
            try:
                self.run()
            except Exception, e:
                rospy.logerr(e)
            rate.sleep()

        self.connection.close()

    def _sql(self, query, read=False):
        result = None
        try:
            self.cursorobj.execute(query)
            result = self.cursorobj.fetchall()
            if not read:
                self.connection.commit()
        except Exception, e:
            rospy.logerr("MySQL: %s" %repr(e))
        return result

    def serviceHandler(self, msg=None):
        print msg
        if msg.type == 'function':
            print "---------------"
            print msg.name
            try:
                if isinstance(eval(msg.data), tuple):
                    result = getattr(self, str(msg.name))(*eval(msg.data))
                elif msg.data != '':
                    result = getattr(self, str(msg.name))(eval(msg.data))
                else:
                    result = getattr(self, str(msg.name))()
                return arom.srv.DriverControlResponse(data = repr(result), done = True)

            except Exception, e:
                rospy.logerr(e)
                return arom.srv.DriverControlResponse(data = repr(e), name = repr("Err"), done = False)

        return arom.srv.DriverControlResponse()


######################################################################################
######################################################################################
####                                                                              ####
####                Driver for       --- Window guard ---                         ####
####               ============================================                   ####
####                                                                              ####
######################################################################################
######################################################################################
        
class WindowGuard(window):
    def init(self):
        rospy.loginfo("WindowGuard requires 'pymlab_drive' service from 'ROSpymlabServer' node")
        rospy.loginfo("run>> 'rosrun arom initPymlab.py'")
        rospy.wait_for_service('pymlab_drive')
        self.pymlab = rospy.ServiceProxy('pymlab_drive', PymlabDrive)
        eval(self.pymlab(device="gpio", method="config_ports", parameters=str((0x0000, 0x0000))).value)
        self.state = 0b0000000000000000
        self.oldstate = self.state
        self.group = 0
        self.off = []

    def run(self):

        if self.state != self.oldstate:
            self.pymlab(device="gpio", method="set_ports", parameters=str(bin(self.state)))
            self.oldstate = self.state

        for off in self.off:
            if time.time() > off[0]:
                self.state = 0
                self.off.remove(off)


    def up(self, group_num, delay = 5):
        rospy.loginfo("Window blind #%i UP" %(group_num*2))
        self.state = 0b0 ^ (0b1 << group_num*2)

        self.off.append([time.time()+delay, group_num*2])

    def down(self, group_num, delay = 5):
        rospy.loginfo("Window blind #%i UP" %(group_num*2+1))
        self.state = 0b0 ^ (0b1 << group_num*2+1)

        self.off.append([time.time()+delay, group_num*2+1])
 

    def connect(self):
        pass




    

if __name__ == '__main__':
    cfg = rospy.get_param("ObservatoryConfig/file")
    print cfg
    with open(cfg) as data_file:
        print data_file
        config = json.load(data_file)
    for x in config:
        if x['name'] == sys.argv[1]:
            weatherStation = locals()[x['driver']](arg = x, config = config)  # ziska jmeno funkce z konfiguracniho souboru v AROM BRAIN a to pak spusti
