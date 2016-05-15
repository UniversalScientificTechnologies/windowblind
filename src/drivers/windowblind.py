#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import time
import datetime
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
import astropy.units as u
from astropy.coordinates import SkyCoord, EarthLocation, AltAz, get_sun
from astropy.time import Time
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
        

        if not rospy.has_param('/blind'):
            print "Vytvareni blind v ROSparam"
            self.properties = {}
            self.properties['group01'] = {'msg_name':'group01', 'mode': 'auto'  , 'close_min_lum': 50, 'close_min_temp': 20, 'blind_down_time': 60, "blind_down_time": 0, "blind_back_time": 0, "max_sun_alt_shade": 0, "blind_afternoon_time": 0, "max_sun_alt_open": 0, "blind_open_time": 0, 'rw': 'r', 'name': "žaluzie okna A", 'description': "", 'status': 'open'    , "rotation": 0, "change": True}
            self.properties['group02'] = {'msg_name':'group02', 'mode': 'manual', 'close_min_lum': 50, 'close_min_temp': 20, 'blind_down_time': 60, "blind_down_time": 0, "blind_back_time": 0, "max_sun_alt_shade": 0, "blind_afternoon_time": 0, "max_sun_alt_open": 0, "blind_open_time": 0, 'rw': 'r', 'name': "žaluzie okna B", 'description': "", 'status': 'open'    , "rotation": 0, "change": True}
            self.properties['group03'] = {'msg_name':'group03', 'mode': 'manual', 'close_min_lum': 50, 'close_min_temp': 20, 'blind_down_time': 60, "blind_down_time": 0, "blind_back_time": 0, "max_sun_alt_shade": 0, "blind_afternoon_time": 0, "max_sun_alt_open": 0, "blind_open_time": 0, 'rw': 'r', 'name': "žaluzie okna C", 'description': "", 'status': 'open'    , "rotation": 0, "change": True}
            self.properties['group04'] = {'msg_name':'group04', 'mode': 'auto'  , 'close_min_lum': 50, 'close_min_temp': 20, 'blind_down_time': 60, "blind_down_time": 0, "blind_back_time": 0, "max_sun_alt_shade": 0, "blind_afternoon_time": 0, "max_sun_alt_open": 0, "blind_open_time": 0, 'rw': 'r', 'name': "žaluzie okna D", 'description': "", 'status': 'open'    , "rotation": 0, "change": True}
            self.properties['group05'] = {'msg_name':'group05', 'mode': 'manual', 'close_min_lum': 50, 'close_min_temp': 20, 'blind_down_time': 60, "blind_down_time": 0, "blind_back_time": 0, "max_sun_alt_shade": 0, "blind_afternoon_time": 0, "max_sun_alt_open": 0, "blind_open_time": 0, 'rw': 'd', 'name': "žaluzie okna E", 'description': "", 'status': 'disabled', "rotation": 0, "change": True}
            self.properties['group06'] = {'msg_name':'group06', 'mode': 'manual', 'close_min_lum': 50, 'close_min_temp': 20, 'blind_down_time': 60, "blind_down_time": 0, "blind_back_time": 0, "max_sun_alt_shade": 0, "blind_afternoon_time": 0, "max_sun_alt_open": 0, "blind_open_time": 0, 'rw': 'd', 'name': "žaluzie okna F", 'description': "", 'status': 'disabled', "rotation": 0, "change": True}
            self.properties['group07'] = {'msg_name':'group07', 'mode': 'manual', 'close_min_lum': 50, 'close_min_temp': 20, 'blind_down_time': 60, "blind_down_time": 0, "blind_back_time": 0, "max_sun_alt_shade": 0, "blind_afternoon_time": 0, "max_sun_alt_open": 0, "blind_open_time": 0, 'rw': 'd', 'name': "žaluzie okna G", 'description': "", 'status': 'disabled', "rotation": 0, "change": True}
            self.properties['group08'] = {'msg_name':'group08', 'mode': 'manual', 'close_min_lum': 50, 'close_min_temp': 20, 'blind_down_time': 60, "blind_down_time": 0, "blind_back_time": 0, "max_sun_alt_shade": 0, "blind_afternoon_time": 0, "max_sun_alt_open": 0, "blind_open_time": 0, 'rw': 'd', 'name': "žaluzie okna H", 'description': "", 'status': 'disabled', "rotation": 0, "change": True}

            rospy.set_param('/blind', self.properties)
        else:
            self.properties = rospy.get_param('/blind')

        print self.properties
        
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


        s_RegisterDriver = rospy.Service('driver/%s/%s' %(self.arg['type'], self.arg['name']), DriverControl, self.serviceHandler)

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
        registred = RegisterDriver(name = self.arg['name'], sname = self.arg['name'], driver = self.arg['driver'], device = self.arg['type'], service = '/driver/%s/%s' %(self.arg['type'], self.arg['name']), status = 1)
        rospy.loginfo("'%s': >> register '%s' driver: '%s'" %(self.arg['name'], 'window', registred))


        ##
        ##  Ovladac pujde ukoncit
        ##
        rate = rospy.Rate(0.2)
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
                #if isinstance(eval(msg.data), tuple):
                #    result = getattr(self, str(msg.name))(*eval(msg.data))
                if msg.data != '':
                    result = getattr(self, str(msg.name))(eval(msg.data))
                else:
                    result = getattr(self, str(msg.name))()
                return arom.srv.DriverControlResponse(data = repr(result), done = True)

            except Exception, e:
                rospy.logerr("serviceHandler: "+repr(e))
                return arom.srv.DriverControlResponse(data = repr(e), name = repr("Err"), done = False)

        return arom.srv.DriverControlResponse()

    def advGetSetting(self, type = None):
        if type == None:
            print "advGetSetting:", self.properties
            return repr(self.properties)
        elif type == 'update':
            raise "Not supported yet"


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
        self.state = 0b0000000000000000
        self.pymlab(device="gpio", method="config_ports", parameters=str((0x0000, 0x0000)))
        self.pymlab(device="gpio", method="set_ports", parameters=str(bin(self.state)))
        self.allup(True)


    def run(self):
        #if self.state != self.oldstate:
        #    self.pymlab(device="gpio", method="set_ports", parameters=str(bin(self.state)))
        #    self.oldstate = self.state

        #for off in self.off:
        #    if time.time() > off[0]:
        #        self.state = 0
        #        self.off.remove(off)

        if rospy.get_param('/weather/wind_alert'):
            allup()
        else:
            for i, blind_id in enumerate(sorted(rospy.get_param('/blind'))):
                blind = rospy.get_param('/blind')[blind_id]
                if blind['rw'] != 'd':
                    print blind
                    if blind['status'] != blind['status_driver']:
                        print "###################"
                        print "     ZMENA DAT"
                        print "^^^^^^^^^^^^^^^^^^^^"
                        if blind['status'] == 'close':
                            self.down(int(blind_id[-1:])-1, blind_id, int(blind['blind_down_time']), int(blind['blind_back_time']))
                        if blind['status'] == 'open':
                            self.up(int(blind_id[-1:])-1, blind_id, int(blind['blind_open_time']), 0)

                    else:
                        print "neni zmena"




    def allup(self, force = False):
        for i, blind_id in enumerate(sorted(rospy.get_param('/blind'))):
            blind = rospy.get_param('/blind')[blind_id]
            if force == True or blind['status'] == 'close':
                print blind_id, blind['rw']
                if blind['rw'] != 'd':
                    print "oteviram", i, blind['blind_open_time']
                    self.up(i, blind_id, delay = int(blind['blind_open_time']), force=force)
                rospy.set_param('/blind/'+blind_id+'/change', False)

    def alldown(self, force = False):
        for i, blind_id in enumerate(sorted(rospy.get_param('/blind'))):
            blind = rospy.get_param('/blind')[blind_id]
            if force == True or blind['status'] == 'open':
                print blind_id, blind['rw']
                if blind['rw'] != 'd':
                    print "zaviram", i, blind['blind_open_time']
                    self.down(i, blind_id, delay = int(blind['blind_down_time']), back_delay=int(blind['blind_back_time']), force=force)
                rospy.set_param('/blind/'+blind_id+'/change', False)


    def up(self, group_num, group, delay = 5, back_delay = 0, force = False):
        rospy.loginfo("Window blind #%i UP for %fs" %(group_num, delay/1000.0))
        self.state = 0b0 ^ (0b1 << group_num*2)
        self.pymlab(device="gpio", method="set_ports", parameters=str(bin(self.state)))
        time.sleep(delay/1000.0)
        self.state = 0
        self.pymlab(device="gpio", method="set_ports", parameters=str(bin(self.state)))
        rospy.set_param('/blind/'+group+"/status", 'open')
        rospy.set_param('/blind/'+group+"/status_driver", 'open')
        rospy.set_param('/blind/'+group+"/rotation", 0)
        rospy.set_param('/blind/'+group+"/rotation_driver", 0)
        if back_delay != 0:
            self.state = 0b0 ^ (0b1 << group_num*2+1)
            self.pymlab(device="gpio", method="set_ports", parameters=str(bin(self.state)))
            time.sleep(back_delay/1000.0)
            self.state = 0
            self.pymlab(device="gpio", method="set_ports", parameters=str(bin(self.state)))
            rospy.set_param('/blind/'+group+"/rotation", back_delay*-1)
            rospy.set_param('/blind/'+group+"/rotation_driver", back_delay*-1)
        return True


    def down(self, group_num, group, delay = 5, back_delay = 0, force = False):
        rospy.loginfo("Window blind #%i UP for %fs" %(group_num, delay/1000.0))
        self.state = 0b0 ^ (0b1 << group_num*2+1)
        self.pymlab(device="gpio", method="set_ports", parameters=str(bin(self.state)))
        time.sleep(delay/1000.0)
        self.state = 0
        self.pymlab(device="gpio", method="set_ports", parameters=str(bin(self.state)))
        rospy.set_param('/blind/'+group+"/status", 'close')
        rospy.set_param('/blind/'+group+"/status_driver", 'close')
        rospy.set_param('/blind/'+group+"/rotation", 0)
        rospy.set_param('/blind/'+group+"/rotation_driver", 0)
        if back_delay != 0:
            rospy.loginfo("Window blind #%i ROTATE for %fs" %(group_num, back_delay/1000.0))
            self.state = 0b0 ^ (0b1 << group_num*2)
            self.pymlab(device="gpio", method="set_ports", parameters=str(bin(self.state)))
            time.sleep(back_delay/1000.0)
            self.state = 0
            self.pymlab(device="gpio", method="set_ports", parameters=str(bin(self.state)))
            rospy.set_param('/blind/'+group+"/rotation", back_delay)
            rospy.set_param('/blind/'+group+"/rotation_driver", back_delay)
        return True
 
    def connect(self):
        pass



class controller(object):
    def __init__(self, arg = None, name = "controller", var = {}, config = {}):
        self.arg = arg
        self.name = self.arg['name']
        self.sname = self.name
        self.variables = var
        self.globalvariables = config
        self.properties = {}

        rospy.init_node(self.arg['name'])
        rospy.loginfo("%s: wait_for_service: 'arom/RegisterDriver'" % self.name)
        rospy.wait_for_service('arom/RegisterDriver')
        rospy.loginfo("%s: >> brain found" % self.name)

        self.connection = mdb.connect(host="localhost", user="root", passwd="root", db="AROM", use_unicode=True, charset="utf8")
        self.cursorobj = self.connection.cursor()

        rate = rospy.Rate(0.5)
        while not rospy.is_shutdown():
            try:

                self.run()
            except Exception, e:
                rospy.logerr(e)
            rate.sleep()

        self.connection.close()

    def run(self):
        astroTime = Time.now()
        altazframe = AltAz(obstime=astroTime, location = EarthLocation(lat=49*u.deg, lon=15*u.deg, height=300*u.m))
        self.sunLoc = get_sun(astroTime).transform_to(altazframe).altaz

        print "#############################"
        groups = rospy.get_param('/blind/')
        self.groups = groups
        for i, group_id in enumerate(sorted(groups)):
            group = groups[group_id]
            if group['rw'] == 'd':
                break

            rospy.loginfo(">> %s" % repr(group_id))
            if not self.isWindOk():
                self.openBlind(group_id)
                rospy.loginfo("blind '%s' is in wind alarm" %group_id)
                break

            if self.isModeAuto(group_id):
                rospy.loginfo("blind '%s' is in auto" %group_id)
                if self.isMorgen():
                    self.areMorgenCondOk(group_id)
                    self.closeBlind(group_id)
                else:
                    self.areAfternoonCondOk(group_id)
                    self.closeBlind(group_id)

            elif self.isModeManual(group_id):
                rospy.loginfo("blind '%s' is in manual" %group_id)
                print group['status'] != group['status_driver'], group['status'], group['status_driver']
                if group['status'] != group['status_driver']:
                    self.moveBlind(group_id, group['status'])

            else:
                rospy.loginfo("blind '%s' is in dimised/manual" %group_id)
                pass

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

    def isWindOk(self):
        return True

    def getMode(self, group):
        return rospy.get_param('/blind/'+group+'/mode', None)

    def isModeAuto(self, group):
        if self.getMode(group) == 'auto':
            return True
        else:
            return False

    def isModeManual(self, group):
        if self.getMode(group) == 'manual':
            return True
        else:
            return False

    def isMorgen(self):
        now = datetime.datetime.now()
        if now.hour < 12:
            return True
        else:
            return False

    def areMorgenCondOk(self, group):
        inTemp = self._sql('SELECT * FROM weather WHERE sensors_id = 9 order by id desc LIMIT 1;')

        print "sun", self.sunLoc.alt*u.deg

        #if self.sunLoc.alt*u.deg > print group

        return True

    def areAfternoonCondOk(self, group):
        inTemp = self._sql('SELECT * FROM weather WHERE sensors_id = 9 order by id desc LIMIT 1;')
        inTemp = self._sql('SELECT * FROM weather WHERE sensors_id = 9 order by id desc LIMIT 1;')
        sunHeight = self.sunLoc.alt*u.deg

        print "sun", self.sunLoc.alt*u.deg
        print group, " >> ", self.groups[group]

        if self.sunLoc.alt*u.deg < self.groups[group]['max_sun_alt_open']:
            rospy.set_param('/blind/'+group+'/status', 'open')
        elif self.sunLoc.alt*u.deg < self.groups[group]['max_sun_alt_shade']:
            rospy.set_param('/blind/'+group+'/rotation', self.groups[group]['blind_afternoon_time'])
        return True

    def moveBlind(self, group, target):
        print "moveBlind", group, target
        if target == 'close':
            self.closeBlind(group)
        if target == 'open':
            self.openBlind(group)

    def closeBlind(self, group):
        rospy.loginfo('CLOSE %s' %(group))
        pass

    def openBlind(self, group):
        rospy.loginfo('OPEN  %s' %(group))
        pass



if __name__ == '__main__':
    cfg = rospy.get_param("ObservatoryConfig/file")
    #print cfg
    with open(cfg) as data_file:
        print data_file
        config = json.load(data_file)
    for x in config:
        if x['name'] == sys.argv[1]:
            weatherStation = locals()[x['driver']](arg = x, config = config)  # ziska jmeno funkce z konfiguracniho souboru v AROM BRAIN a to pak spusti
