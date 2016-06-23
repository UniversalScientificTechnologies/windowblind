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
        self.name = self.arg['name']
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
        self.pymlab(device="blind", method="config_ports", parameters=str((0x00, 0x00)))
        self.pymlab(device="blind", method="set_ports", parameters=str((~self.state, 0x00000000)))
        self.allup(True)


    def run(self):
        print "#############################"
        if not self.isWindOk():
            self.allup()
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
                                self.up(int(blind_id[-1:])-1, blind_id, int(blind['blind_open_time']), 0)
                                rospy.set_param('/blind/'+blind_id+"/status_driver", 'open')
                        
                        elif blind['rotation'] != blind['rotation_driver']:
                            logging.info("Zmena rotace:")
                            print "###################"
                            print "     ZMENA ROTACE"
                            print "^^^^^^^^^^^^^^^^^^^^"
                            if blind['rotation'] > blind['rotation_driver']:
                                self.down(int(blind_id[-1:])-1, blind_id, int(blind['blind_afternoon_time']), 0)
                                rospy.set_param('/blind/'+blind_id+"/rotation_driver", blind['rotation'])
                                rospy.set_param('/blind/'+blind_id+"/rotation", blind['rotation'])
                            elif blind['rotation'] < blind['rotation_driver']:
                                self.up(int(blind_id[-1:])-1, blind_id, int(blind['blind_afternoon_time']), 0)
                                rospy.set_param('/blind/'+blind_id+"/rotation_driver", blind['rotation'])
                                rospy.set_param('/blind/'+blind_id+"/rotation", blind['rotation'])
                        
                        else:
                            print "neni zmena"
                else:
                    print ""


    def allup(self, force = False):
        for i, blind_id in enumerate(sorted(rospy.get_param('/blind'))):
            blind = rospy.get_param('/blind')[blind_id]
            if (force == True or blind['status'] == 'close') and 'group' in blind_id:
                print blind_id, blind['rw']
                if blind['rw'] != 'd':
                    print "====oteviram==vse====", i, blind['blind_open_time']
                    self.up(int(blind_id[-1:])-1, blind_id, delay = int(blind['blind_open_time']), force=force)
                rospy.set_param('/blind/'+blind_id+'/change', False)


    def alldown(self, force = False):
        for i, blind_id in enumerate(sorted(rospy.get_param('/blind'))):
            blind = rospy.get_param('/blind')[blind_id]
            if (force == True or blind['status'] == 'open') and 'group' in blind_id:
                print blind_id, blind['rw']
                if blind['rw'] != 'd':
                    print "====zaviram==vse=====", i, blind['blind_open_time']
                    self.down(int(blind_id[-1:])-1, blind_id, delay = int(blind['blind_down_time']), back_delay=int(blind['blind_back_time']), force=force)
                rospy.set_param('/blind/'+blind_id+'/change', False)


    def up(self, group_num, group, delay = 5, back_delay = 0, force = False):
        rospy.loginfo("Window blind #%i **UP** for %fs" %(group_num, delay/1000.0))
        self.state = 0b0 ^ (0b1 << group_num*2)
        self.pymlab(device="blind", method="set_ports", parameters=str((~self.state, 0x00000000)))
        time.sleep(delay/1000.0)
        self.state = 0
        self.pymlab(device="blind", method="set_ports", parameters=str((~self.state, 0x00000000)))
        #rospy.set_param('/blind/'+group+"/status", 'open')
        #rospy.set_param('/blind/'+group+"/status_driver", 'open')
        print "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^"
        print "get_param", rospy.get_param('/blind/'+group+"/status"), rospy.get_param('/blind/'+group+"/status_driver")
        rospy.set_param('/blind/'+group+"/rotation", 0)
        rospy.set_param('/blind/'+group+"/rotation_driver", 0)
        if back_delay != 0:
            time.sleep(1000)
            self.state = 0b0 ^ (0b1 << group_num*2+1)
            self.pymlab(device="blind", method="set_ports", parameters=str((~self.state, 0x00000000)))
            time.sleep(back_delay/1000.0)
            self.state = 0
            self.pymlab(device="blind", method="set_ports", parameters=str((~self.state, 0x00000000)))
            rospy.set_param('/blind/'+group+"/rotation", back_delay*-1)
            rospy.set_param('/blind/'+group+"/rotation_driver", back_delay*-1)
        return True


    def down(self, group_num, group, delay = 5, back_delay = 0, force = False):
        rospy.loginfo("Window blind #%i **DOWN** for %fs" %(group_num, delay/1000.0))
        self.state = 0b0 ^ (0b1 << group_num*2+1)
        self.pymlab(device="blind", method="set_ports", parameters=str((~self.state, 0x00000000)))
        time.sleep(delay/1000.0)
        self.state = 0
        self.pymlab(device="blind", method="set_ports", parameters=str((~self.state, 0x00000000)))
        #rospy.set_param('/blind/'+group+"/status", 'close')
        #rospy.set_param('/blind/'+group+"/status_driver", 'close')
        print "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^"
        print "get_param", rospy.get_param('/blind/'+group+"/status"), rospy.get_param('/blind/'+group+"/status_driver")
        rospy.set_param('/blind/'+group+"/rotation", 0)
        rospy.set_param('/blind/'+group+"/rotation_driver", 0)
        if back_delay != 0:
            time.sleep(1)
            rospy.loginfo("Window blind #%i **ROTATE** for %fs" %(group_num, back_delay/1000.0))
            logging.info("Window blind #%i **ROTATE** for %fs", group_num, delay/1000.0)
            self.state = 0b0 ^ (0b1 << group_num*2)
            self.pymlab(device="blind", method="set_ports", parameters=str((~self.state, 0x00000000)))
            time.sleep(back_delay/1000.0)
            self.state = 0
            self.pymlab(device="blind", method="set_ports", parameters=str((~self.state, 0x00000000)))
            rospy.set_param('/blind/'+group+"/rotation", back_delay)
            rospy.set_param('/blind/'+group+"/rotation_driver", back_delay)
        return True
 
    def connect(self):
        pass

    def isWindOk(self):
        wind_limit = rospy.get_param('/blind/global/max_wind', 50)
        wind_limit_delay = rospy.get_param('/blind/global/max_wind_delay', 60*48)*60
        mtime = time.time()
        damage = float(self._sql('SELECT MAX(value) FROM weather WHERE sensors_id = 13 and date > %f;' %int(mtime-3600*24) )[0][0])
        actual = float(self._sql('SELECT AVG(value) FROM weather WHERE sensors_id = 13 and date > %f;' %int(mtime- 300) )[0][0])
        if actual < wind_limit and damage > 1:
            return True
        else:
            return False



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

        print ""
        print "#############################"
        groups = rospy.get_param('/blind/')
        self.groups = groups
        self.group  = groups
        self.inTemp = float(self._sql('SELECT value FROM weather WHERE sensors_id = 17 order by id desc LIMIT 1;')[0][0])
        self.outLum = float(self._sql('SELECT AVG(value) FROM weather WHERE sensors_id = 16 and date > %i;' %(int(time.time() - int(rospy.get_param('/blind/global/min_light_delay', 30)*60))) )[0][0])
        
        for i, group_id in enumerate(sorted(groups)):
            print "=====", i, "====", group_id, "===="
            if 'group' in group_id:
                group = groups[group_id]
                if group['rw'] == 'd':
                    break

                rospy.loginfo(">> %s" % repr(group_id))
                if not self.isWindOk():
                    self.openBlind(group_id)
                    rospy.logerr("blind '%s' is in wind alarm" %group_id)
                    print "chyba vetru"

                else:
                    if self.isModeAuto(group_id):
                        print "vitr OK - automaticky mod - ",
                        rospy.loginfo("blind '%s' is in auto" %group_id)
                        if self.isMorgen(group_id):
                            print "je dopoledne - ",
                            self.areMorgenCondOk(group_id)
                        else:
                            print "je odpoledne - ",
                            self.areAfternoonCondOk(group_id)
                            #self.closeBlind(group_id)

                    elif self.isModeManual(group_id):
                        print "vitr OK - manualni mod - "
                        '''
                        print "pohyb", group['status'] != group['status_driver'], group['status'], group['status_driver']
                        #if group['status'] == 'open':
                        #    print "STATUS **********************",
                        #else:
                        #    print "STATUS ######################",
                        #if group['status_driver'] == 'open':
                        #    print "  DRIVER  **********************"
                        #else:
                        #    print " DRIVER ######################"
                        #if group['status'] != group['status_driver']:
                        #    self.moveBlind(group_id, group['status'])
                        '''


                    else:
                        print "vitr OK - chyba modu - ",
                        rospy.loginfo("blind '%s' is in dimised/manual" %group_id)
                        pass
                        print ""

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
        wind_limit = int(rospy.get_param('/blind/global/max_wind', 50))
        wind_limit_delay = int(rospy.get_param('/blind/global/max_wind_delay', 60*48)*60)
        mtime = time.time()
        damage = float(self._sql('SELECT MAX(value) FROM weather WHERE sensors_id = 13 and date > %f;' %int(mtime-3600*24) )[0][0])
        actual = float(self._sql('SELECT MAX(value) FROM weather WHERE sensors_id = 13 and date > %f;' %int(mtime-wind_limit_delay) )[0][0])
        print "actual wind", actual, "damage", damage
        if actual < wind_limit and damage > 1:
            rospy.set_param('/blind/global/message', "systém funguje, výška Slunce je %f&#176." %(float(self.sunLoc.alt.degree)))
            return True
        else:
            rospy.set_param('/blind/global/message', "wind alarm!!!")
            return False

    def getMode(self, group):
        return rospy.get_param('/blind/'+group+'/mode', None)

    def isModeAuto(self, group):
        if self.getMode(group) == 'auto':
            return True
        else:
            return False

    def isModeManual(self, group):
        if self.getMode(group) == 'manual':
            #self.closeBlind(group)
            return True
        else:
            return False

    def isMorgen(self, group):
        now = datetime.datetime.now()
        sunHeight = float(self.sunLoc.alt.degree)
        if now.hour < 12 or sunHeight > float(self.groups[group]['max_sun_alt_shade']):
            return True
        else:
            return False

    def areMorgenCondOk(self, group):
        # podminky rano:
        # >> min cas
        # >> min jas po urcitou dobu

        #inTemp = float(self._sql('SELECT value FROM weather WHERE sensors_id = 17 order by id desc LIMIT 1;')[0][0])
        #outLum = float(self._sql('SELECT AVG(value) FROM weather WHERE sensors_id = 16 and date > %i;' %(int(time.time() - int(rospy.get_param('/blind/global/min_light_delay', 30)*60))) )[0][0])
        print "rano - lum: %s, in temp %s" %(repr(self.outLum), repr(self.inTemp))


        #if inTemp self.group[group]['close_min_temp'] > and outLum > self.group[group]['close_min_lum']:
        now = datetime.datetime.now()
        if (now.hour*60+now.minute) > 7*60  and self.outLum > float(self.group['global']['min_light']) and self.inTemp > float(self.group['global']['min_temp']):
            rospy.loginfo("ZAVRIT")
            self.closeBlind(group)
            rospy.loginfo("ZAVRIT")
            return True
        else:
            return False

    def areAfternoonCondOk(self, group):
        # podminky odpeledne:
        # >> max vyska 1
        # >> max vyska 2

        sunHeight = float(self.sunLoc.alt.degree)
        print "vyska slunce: ", sunHeight, "open, shade:", self.groups[group]['max_sun_alt_open'], self.groups[group]['max_sun_alt_shade'],
        
        if sunHeight < float(self.groups[group]['max_sun_alt_open']):  #vyska slunce pro uplne otevreni
            print "-- Otevrit kompletne"
            self.openBlind(group)
            rospy.loginfo("OTEVRIT")
        elif sunHeight < float(self.groups[group]['max_sun_alt_shade']) and self.outLum > float(self.group['global']['min_light']):  #vyska slunce pro pootoceni
            print "-- privrit"
            rospy.loginfo("OTOCIT")
            self.rotateBlind(group)
        else:
            print "-- zavreno"
        return True

    '''
    def moveBlind(self, group, target):
        print "moveBlind---------", group, target
        if target == 'close':
            self.closeBlind(group)
        if target == 'open':
            self.openBlind(group)
    '''

    def closeBlind(self, group):
        rospy.loginfo('CLOSE %s' %(group))
        rospy.set_param('/blind/'+group+'/status', 'close')
        pass

    def openBlind(self, group):
        rospy.loginfo('OPEN  %s' %(group))
        rospy.set_param('/blind/'+group+'/status', 'open')
        pass

    def rotateBlind(self, group):
        rospy.loginfo('ROTATE  %s' %(group))
        rospy.set_param('/blind/'+group+'/rotation', self.groups[group]['blind_afternoon_time'])
        pass




if __name__ == '__main__':

    logging.basicConfig(filename='windowBlind.log', level=logging.INFO,format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

    cfg = rospy.get_param("ObservatoryConfig/file")
    #print cfg
    with open(cfg) as data_file:
        print data_file
        config = json.load(data_file)
    for x in config:
        if x['name'] == sys.argv[1]:
            weatherStation = locals()[x['driver']](arg = x, config = config)  # ziska jmeno funkce z konfiguracniho souboru v AROM BRAIN a to pak spusti
