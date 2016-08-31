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
import MySQLdb as mdb
import httplib2

import logging
#logger = logging.getLogger('__name__')
#hdlr = logging.FileHandler('/home/odroid/WindowBlind.log')
#formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
#hdlr.setFormatter(formatter)
#logger.addHandler(hdlr) 
#logger.setLevel(logging.WARNING)


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
        self.name = name
        self.sname = self.name
        self.variables = var
        self.globalvariables = config
        

        if not rospy.has_param('/blind'):
            print "Vytvareni blind v ROSparam"
            self.properties = {}
            self.properties['group01'] = {'msg_name':'group01', 'mode': 'manual', 'close_min_lum': 50, 'close_min_temp': 20, 'blind_down_time': 5000, "blind_back_time": 100, "max_sun_alt_shade": 45, "blind_afternoon_time": 100, "max_sun_alt_open": 10, "blind_open_time": 6000, 'rw': 'r', 'name': "žaluzie okna A", 'description': "", 'status': 'open'    , "rotation": 0, "change": True}
            self.properties['group02'] = {'msg_name':'group02', 'mode': 'manual', 'close_min_lum': 50, 'close_min_temp': 20, 'blind_down_time': 5000, "blind_back_time": 100, "max_sun_alt_shade": 45, "blind_afternoon_time": 100, "max_sun_alt_open": 10, "blind_open_time": 6000, 'rw': 'r', 'name': "žaluzie okna B", 'description': "", 'status': 'open'    , "rotation": 0, "change": True}
            self.properties['group03'] = {'msg_name':'group03', 'mode': 'manual', 'close_min_lum': 50, 'close_min_temp': 20, 'blind_down_time': 5000, "blind_back_time": 100, "max_sun_alt_shade": 45, "blind_afternoon_time": 100, "max_sun_alt_open": 10, "blind_open_time": 6000, 'rw': 'r', 'name': "žaluzie okna C", 'description': "", 'status': 'open'    , "rotation": 0, "change": True}
            self.properties['group04'] = {'msg_name':'group04', 'mode': 'manual', 'close_min_lum': 50, 'close_min_temp': 20, 'blind_down_time': 5000, "blind_back_time": 100, "max_sun_alt_shade": 45, "blind_afternoon_time": 100, "max_sun_alt_open": 10, "blind_open_time": 6000, 'rw': 'r', 'name': "žaluzie okna D", 'description': "", 'status': 'open'    , "rotation": 0, "change": True}
            self.properties['group05'] = {'msg_name':'group05', 'mode': 'manual', 'close_min_lum': 50, 'close_min_temp': 20, 'blind_down_time': 5000, "blind_back_time": 100, "max_sun_alt_shade": 45, "blind_afternoon_time": 100, "max_sun_alt_open": 10, "blind_open_time": 6000, 'rw': 'd', 'name': "žaluzie okna E", 'description': "", 'status': 'disabled', "rotation": 0, "change": True}
            self.properties['group06'] = {'msg_name':'group06', 'mode': 'manual', 'close_min_lum': 50, 'close_min_temp': 20, 'blind_down_time': 5000, "blind_back_time": 100, "max_sun_alt_shade": 45, "blind_afternoon_time": 100, "max_sun_alt_open": 10, "blind_open_time": 6000, 'rw': 'd', 'name': "žaluzie okna F", 'description': "", 'status': 'disabled', "rotation": 0, "change": True}
            self.properties['group07'] = {'msg_name':'group07', 'mode': 'manual', 'close_min_lum': 50, 'close_min_temp': 20, 'blind_down_time': 5000, "blind_back_time": 100, "max_sun_alt_shade": 45, "blind_afternoon_time": 100, "max_sun_alt_open": 10, "blind_open_time": 6000, 'rw': 'd', 'name': "žaluzie okna G", 'description': "", 'status': 'disabled', "rotation": 0, "change": True}
            self.properties['group08'] = {'msg_name':'group08', 'mode': 'manual', 'close_min_lum': 50, 'close_min_temp': 20, 'blind_down_time': 5000, "blind_back_time": 100, "max_sun_alt_shade": 45, "blind_afternoon_time": 100, "max_sun_alt_open": 10, "blind_open_time": 6000, 'rw': 'd', 'name': "žaluzie okna H", 'description': "", 'status': 'disabled', "rotation": 0, "change": True}

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


        s_RegisterDriver = rospy.Service('driver/%s/%s' %('blind', self.name), DriverControl, self.serviceHandler)

        ##
        ##  Ceka to na spusteni AROMbrain nodu
        ##

        rospy.init_node(self.name)
        rospy.loginfo("%s: wait_for_service: 'arom/RegisterDriver'" % self.name)
        rospy.wait_for_service('arom/RegisterDriver')
        rospy.loginfo("%s: >> brain found" % self.name)

        ##
        ##  Registrace zarizeni
        ##  >>> Arom returns 1 - OK, 0 - False
        ##

        RegisterDriver = rospy.ServiceProxy('arom/RegisterDriver', arom.srv.RegisterDriver)
        registred = RegisterDriver(name = self.name, sname = self.name, driver = 'blind', device = 'blind', service = '/driver/%s/%s' %('blind', 'blind'), status = 1)
        rospy.loginfo("'%s': >> register '%s' driver: '%s'" %(self.name, 'window', repr(registred)))


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
######################################################################################class WindowGuard(window):
    def init(self):

        rospy.loginfo("WindowGuard requires 'pymlab_drive' service from 'ROSpymlabServer' node")
        rospy.loginfo("run>> 'rosrun arom initPymlab.py'")
        rospy.wait_for_service('pymlab_drive')
        self.pymlab = rospy.ServiceProxy('pymlab_drive', PymlabDrive)
        self.state = 0b0000000000000000
        self.pymlab(device="blind", method="config_ports", parameters=str((0x00, 0x00)))
        self.pymlab(device="blind", method="set_ports", parameters=str((~self.state, 0x00000000)))
        self.allup(True)


    def run(self):
        print "#############################"
        if not self.isWindOk():
            self.allup(True)
        else:
            for i, blind_id in enumerate(sorted(rospy.get_param('/blind'))):
                print "======", blind_id, "==========",
                blind = rospy.get_param('/blind')[blind_id]
                if 'group' in blind_id:
                    if blind['rw'] != 'd':
                        print "target >>>>>", blind['status'], blind['status_driver']
                        if blind['status'] != blind['status_driver']:
                            logging.info("Zmena dat:")
                            print "###################"
                            print "     ZMENA DAT"
                            print "^^^^^^^^^^^^^^^^^^^^"
                            if blind['status'] == 'close':
                                self.down(int(blind_id[-1:])-1, blind_id, int(blind['blind_down_time']), int(blind['blind_back_time']))
                                rospy.set_param('/blind/'+blind_id+"/status_driver", 'close')
                            elif blind['status'] == 'open':
                                self.up(int(blind_id[-1:])-1, blind_id, delay_ms = int(blind['blind_open_time']))
                                rospy.set_param('/blind/'+blind_id+"/status_driver", 'open')
                        
                        elif blind['rotation'] != blind['rotation_driver']:
                            logging.info("Zmena rotace:")
                            print "###################"
                            print "     ZMENA ROTACE"
                            print "^^^^^^^^^^^^^^^^^^^^"
                            if blind['rotation'] > blind['rotation_driver']:
                                self.down(int(blind_id[-1:])-1, blind_id, delay_ms = int(blind['blind_afternoon_time']))
                                rospy.set_param('/blind/'+blind_id+"/rotation_driver", blind['rotation'])
                                rospy.set_param('/blind/'+blind_id+"/rotation", blind['rotation'])
                            elif blind['rotation'] < blind['rotation_driver']:
                                self.up(int(blind_id[-1:])-1, blind_id, delay_ms = int(blind['blind_afternoon_time']))
                                rospy.set_param('/blind/'+blind_id+"/rotation_driver", blind['rotation'])
                                rospy.set_param('/blind/'+blind_id+"/rotation", blind['rotation'])
                        
                        else:
                            print "neni zmena"
                else:
                    print ""


    def allup(self, force = False):
        print "====oteviram==vse===="
        for i, blind_id in enumerate(sorted(rospy.get_param('/blind'))):
            blind = rospy.get_param('/blind')[blind_id]
            if (force == True or blind['status'] == 'close') and 'group' in blind_id:
                print 'blind_id:', blind_id, "blind['rw']", blind['rw'], 'oteviram po dobu:', blind['blind_open_time']
                if blind['rw'] != 'd':
                    self.up(int(blind_id[-1:])-1, blind_id, delay_ms = int(blind['blind_open_time']), force=force)
                    rospy.set_param('/blind/'+blind_id+'/status', 'open')
                    rospy.set_param('/blind/'+blind_id+'/status_driver', 'open')
                rospy.set_param('/blind/'+blind_id+'/change', False)


    def alldown(self, force = False):
        for i, blind_id in enumerate(sorted(rospy.get_param('/blind'))):
            blind = rospy.get_param('/blind')[blind_id]
            if (force == True or blind['status'] == 'open') and 'group' in blind_id:
                print blind_id, blind['rw']
                if blind['rw'] != 'd':
                    print "====zaviram==vse=====", i, blind['blind_open_time']
                    self.down(int(blind_id[-1:])-1, blind_id, delay_ms = int(blind['blind_down_time']), back_delay_ms=int(blind['blind_back_time']), force=force)
                rospy.set_param('/blind/'+blind_id+'/change', False)


    def up(self, group_num, group, delay_ms = 250, back_delay_ms = 0, force = False):
        #vytvoreni promennych, kde jsou sekundy (ziskane jednotky jsou ms)
        delay = delay_ms/1000.0
        back_delay = back_delay_ms/1000.0

        rospy.loginfo("Window blind #%i **UP** for %fs" %(group_num, delay))

        #sepne spravny okruh smerem nahoru
        state = 0b0 ^ (0b1 << group_num*2)
        self.pymlab(device="blind", method="set_ports", parameters=str((~state, 0x00000000)))
        #ceka se pozadovany cas
        time.sleep(delay)
        self.pymlab(device="blind", method="set_ports", parameters=str((~0x00000000, 0x00000000)))
        rospy.set_param('/blind/'+group+"/rotation", 0)
        rospy.set_param('/blind/'+group+"/rotation_driver", 0)
        if back_delay > 0:
            time.sleep(1)
            state = 0b0 ^ (0b1 << group_num*2+1)
            self.pymlab(device="blind", method="set_ports", parameters=str((~state, 0x00000000)))
            time.sleep(back_delay/1000.0)
            self.pymlab(device="blind", method="set_ports", parameters=str((~0x00000000, 0x00000000)))
            rospy.set_param('/blind/'+group+"/rotation", back_delay*-1)
            rospy.set_param('/blind/'+group+"/rotation_driver", back_delay*-1)
        time.sleep(0.500)
        return True


    def down(self, group_num, group, delay_ms = 250, back_delay_ms = 0, force = False):
        #vytvoreni promennych, kde jsou sekundy (ziskane jednotky jsou ms)
        delay = delay_ms/1000.0
        back_delay = back_delay_ms/1000.0

        rospy.loginfo("Window blind #%i **DOWN** for %fs" %(group_num, delay))

        #sepne spravny okruh smerem dolu
        state = 0b0 ^ (0b1 << group_num*2+1)
        self.pymlab(device="blind", method="set_ports", parameters=str((~state, 0x00000000)))
        #ceka se pozadovany cas
        time.sleep(delay)
        self.pymlab(device="blind", method="set_ports", parameters=str((~0x00000000, 0x00000000)))
        print "get_param - statut:", rospy.get_param('/blind/'+group+"/status"),'driver:', rospy.get_param('/blind/'+group+"/status_driver")
        rospy.set_param('/blind/'+group+"/rotation", 0)
        rospy.set_param('/blind/'+group+"/rotation_driver", 0)
        if back_delay > 0:
            time.sleep(1)
            rospy.loginfo("Window blind #%i **ROTATEup** for %fs" %(group_num, back_delay*1.0))
            state = 0b0 ^ (0b1 << group_num*2)
            self.pymlab(device="blind", method="set_ports", parameters=str((~state, 0x00000000)))
            time.sleep(back_delay)
            self.pymlab(device="blind", method="set_ports", parameters=str((~0x00000000, 0x00000000)))
            rospy.set_param('/blind/'+group+"/rotation", back_delay_ms)
            rospy.set_param('/blind/'+group+"/rotation_driver", back_delay_ms)
        time.sleep(0.500)
        return True
 
    def connect(self):
        pass

    def isWindOk(self):
        wind_limit = rospy.get_param('/blind/global/max_wind', 50)
        wind_limit_delay = rospy.get_param('/blind/global/max_wind_delay', 60*48)*60
        mtime = time.time()
        damage = float(self._sql('SELECT MAX(value) FROM weather WHERE sensors_id = 4 and date > %f;' %int(mtime-3600*24) )[0][0])
        actual = float(self._sql('SELECT AVG(value) FROM weather WHERE sensors_id = 4 and date > %f;' %int(mtime- 300) )[0][0])
        if actual < wind_limit and damage > 0:
            return True
        else:
            return False






if __name__ == '__main__':

    logging.basicConfig(filename='windowBlind.log', level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

    cfg = rospy.get_param("ObservatoryConfig/file")
    #print cfg
    with open(cfg) as data_file:
        print data_file
        config = json.load(data_file)
    
    weatherStation = window(config = config)  # ziska jmeno funkce z konfiguracniho souboru v AROM BRAIN a to pak spusti
