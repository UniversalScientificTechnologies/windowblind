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



class controller(object):
    def __init__(self, arg = None, name = "controller", var = {}, config = {}):
        self.name = name
        self.sname = self.name
        self.variables = var
        self.globalvariables = config
        self.properties = {}

        rospy.init_node(name)
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
        self.inTemp = float(self._sql('SELECT value FROM weather WHERE sensors_id = 5 order by id desc LIMIT 1;')[0][0])
        self.outLum = float(self._sql('SELECT AVG(value) FROM weather WHERE sensors_id = 3 and date > %i;' %(int(time.time() - int(rospy.get_param('/blind/global/min_light_delay', 30)*60))) )[0][0])
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
        damage = float(self._sql('SELECT MAX(value) FROM weather WHERE sensors_id = 4 and date > %f;' %int(mtime-3600*24) )[0][0])
        actual = float(self._sql('SELECT MAX(value) FROM weather WHERE sensors_id = 4 and date > %f;' %int(mtime-wind_limit_delay) )[0][0])
        print "actual wind", actual, "damage", damage
        if actual < wind_limit and damage > 0:
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

    logging.basicConfig(filename='windowBlind.log', level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

    cfg = rospy.get_param("ObservatoryConfig/file")
    #print cfg
    with open(cfg) as data_file:
        print data_file
        config = json.load(data_file)
    
    weatherStation = controller(config = config)  # ziska jmeno funkce z konfiguracniho souboru v AROM BRAIN a to pak spusti
