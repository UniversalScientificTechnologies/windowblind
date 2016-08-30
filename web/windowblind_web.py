#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
import datetime
import os
import tornado.ioloop
import tornado.web
from tornado import web
from tornado import ioloop
from tornado import websocket
from tornado import auth
from tornado import escape
from tornado import httpserver
from tornado import options
from tornado import web
import json
import ephem

import std_msgs
from std_msgs.msg import String
from std_msgs.msg import Float32
from windowblind.srv import *
#from windowblind.msg import *
import windowblind
import rospy

from astropy.time import Time
import rosapi
import MySQLdb as mdb

#print rosapi.get_nodes()


rospy.logerr("wait_for_service /arom/NodeInfo")
print "wait_for_service /arom/NodeInfo"
rospy.wait_for_service('/arom/NodeInfo')
print "OK"
#brain_nodeinfo = rospy.ServiceProxy('/arom/NodeInfo', arom.srv.NodeInfo)

def get_devices():
    try:
        brain_nodeinfo = rospy.ServiceProxy('/arom/NodeInfo', windowblind.srv.NodeInfo)
        resp1 = brain_nodeinfo(type = 'GetAllNodes')
        print resp1.data
        return resp1
    except rospy.ServiceException, e:
        print "Service call failed: %s"%e


def _sql(query, read=False):
	try:
            print "#>", query
            connection = mdb.connect(host="localhost", user="root", passwd="root", db="AROM", use_unicode=True, charset="utf8")
            cursorobj = connection.cursor()
            result = None
            try:
                    cursorobj.execute(query)
                    result = cursorobj.fetchall()
                    if not read:
                        connection.commit()
            except Exception, e:
                    print "Err", e
            connection.close()
            return result
        except e:
            return [[0]]

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")

class Overview(web.RequestHandler):
    #@tornado.web.asynchronous
    def get(self, addres=None):
        #print "web", addres
        self.render("www/layout/dash/publicOverview.html", title = "AROM", leftmenu = leftmenu, actual = '#', _sql=_sql)


class Observatory(web.RequestHandler):
    #@tornado.web.asynchronous
    def get(self, addres=None):
        #print "web", addres
        self.render("www/layout/dash/observatory.html", title = "AROM control center | observatory", leftmenu = leftmenu, actual = 'observatory', _sql=_sql)

class Obs_weather_datatable(web.RequestHandler):
    #@tornado.web.asynchronous
    def get(self, addres=None):
        arg_data = self.get_argument('data', False)
        arg_type = self.get_argument('type', False)
        arg_sens = self.get_argument('sens', 0)
        print arg_type, arg_data, "---------"
        if arg_data == 'weather' and arg_type == 'json':
            data = _sql('SELECT date, avg(value), sensors_id from weather GROUP BY date div (60*10), sensors_id  ORDER BY date;')
            self.write('[\n\r['+str(float(data[0][0])*1000)+','+str(round(float(data[0][1]),3))+','+str(round(float(data[0][2]),3))+']')
            for row in data:
                self.write(',['+str(float(row[0])*1000)+','+str(round(float(row[1]),3))+','+str(round(float(row[2]),3))+']\n\r')
                #sout.append([float(row[0]), float(row[1])])
            self.finish('\n\r]')

        elif arg_data == 'AROMconfig' and arg_type == 'json':
            pass
        else:
            data = _sql('SELECT weather.id, weather.date, weather.sensors_id, weather.value, sensors.sensor_name, sensors.sensor_quantity_mark FROM weather JOIN sensors ON weather.sensors_id = sensors.sensors_id WHERE (date > %f) GROUP BY sensors_id ORDER BY weather.sensors_id;' %(Time.now().unix-60))
            #print data
            string = '<table class="table">'
            for row in data:
                string += '<tr><td>'+datetime.datetime.fromtimestamp(float(row[1])).strftime('%Y-%m-%d %H:%M:%S')+'</td><td>'+str(row[4])+'</td><td>'+str(row[2])+'</td><td>'+str(row[3])+" "+row[5]+'</td></tr>'
            string += '</table>'
            self.finish(string)



class processing(web.RequestHandler):
    #@tornado.web.asynchronous
    def get(self, arg = None):
        rospy.logerr("processing")
        print "processing", arg
        coord = self.get_argument("coord", False)
        if coord:
            param = eval(coord)
            #print "param", param
            if param['typ'] == 'AltAz2RaDec':
                out = SkyCoord(alt=param['alt'], az=param['az'], unit='deg', obstime = Time.now(), frame = 'altaz', location = observatory)
                sout = {
                    "ra": out.icrs.ra.degree,
                    "dec": out.icrs.dec.degree,
                    #"alt": param['alt'],
                    #"az": param['az'],
                    }
                #print sout
                self.finish(escape.json_encode(sout))

                
            elif param['typ'] == 'RaDec2AltAz':
                # = loc.transform_to(AltAz(obstime = Time.now(), location=self.observatory))
                #F_az = (np.abs(self.horizont[:,0] - altaz.az.degree)).argmin()
                #local_horizont = self.horizont[F_az]
                pass
        else:
            rospy.logerr("Chyba v processing")





class BlindApi(web.RequestHandler):
    #@tornado.web.asynchronous
    def get(self, address=None):
        print "############################"
        address = address.split("/")
        print "web", address

        if address[0] == 'weather':
            print "WEATHER",
            if address[1] == 'maxWindLast':
                data = _sql('SELECT weather.id, weather.date, max(weather.value), sensors.sensor_name, sensors.sensor_quantity_mark FROM weather JOIN sensors ON weather.sensors_id = sensors.sensors_id WHERE (date > %f) GROUP BY sensors_id ORDER BY weather.sensors_id;' %(Time.now().unix-address[3]*60))
                #print data
                self.render(data)

            else:
                arg_data = self.get_argument('data', False)
                arg_type = self.get_argument('type', False)
                arg_sens = self.get_argument('sens', 0)
                #print arg_type, arg_data, "---------"
                if arg_data == 'weather' and arg_type == 'json':
                    data = _sql('SELECT date, avg(value), sensors_id from weather GROUP BY date div (60*10), sensors_id  ORDER BY date;')
                    self.write('[\n\r['+str(float(data[0][0])*1000)+','+str(round(float(data[0][1]),3))+','+str(round(float(data[0][2]),3))+']')
                    for row in data:
                        self.write(',['+str(float(row[0])*1000)+','+str(round(float(row[1]),3))+','+str(round(float(row[2]),3))+']\n\r')
                        #sout.append([float(row[0]), float(row[1])])
                    self.finish('\n\r]')

                elif arg_data == 'AROMconfig' and arg_type == 'json':
                    pass
                else:
                    data = _sql('SELECT weather.id, weather.date, weather.sensors_id, weather.value, sensors.sensor_name, sensors.sensor_quantity_mark FROM weather JOIN sensors ON weather.sensors_id = sensors.sensors_id WHERE (date > %f) GROUP BY sensors_id ORDER BY weather.sensors_id;' %(Time.now().unix-60))
                    #print data
                    string = '<table class="table">'
                    for row in data:
                        string += '<tr><td>'+datetime.datetime.fromtimestamp(float(row[1])).strftime('%Y-%m-%d %H:%M:%S')+'</td><td>'+str(row[4])+'</td><td>'+str(row[2])+'</td><td>'+str(round(float(row[3]),2))+" "+row[5]+'</td></tr>'
                        #string += '<br>' + str(row)
                    string += '</table>'
                    self.finish(string)

        elif address[0] == 'update':
            print "UPDATE GET"


        else:
            print "NEZNAMY PARAMETR"
            print "---------------"
            #self.render("www/layout/dash/observatory.html", title = "AROM control center | observatory", leftmenu = leftmenu, actual = 'observatory', _sql=_sql)
            self.finish("loading...")

    def post(self, address=None):
        address = address.split("/")
        if address[0] == 'update':
            print "UPDATE POST"
            #print address

            id = self.get_argument('id')

            if id == 'global':
                min_light = self.get_argument('min_light')
                min_light_delay = self.get_argument('min_light_delay')
                min_temp = self.get_argument('min_temp')
                max_wind = self.get_argument('max_wind')
                max_wind_delay = self.get_argument('max_wind_delay')

                rospy.set_param('/blind/global/min_light', min_light)
                rospy.set_param('/blind/global/min_light_delay', min_light_delay)
                rospy.set_param('/blind/global/min_temp', min_temp)
                rospy.set_param('/blind/global/max_wind', max_wind)
                rospy.set_param('/blind/global/max_wind_delay', max_wind_delay)

            elif 'group' in id:
                '''
                // mode
                #// close_min_lum
                #// close_min_temp
                // blind_down_time
                // blind_back_time
                // max_sun_alt_shade
                // blind_afternoon_time
                // max_sun_alt_open
                // blind_open_time
                '''
                mode = self.get_argument('mode')
                #close_min_lum = self.get_argument('close_min_lum')
                #close_min_temp = self.get_argument('close_min_temp')
                blind_down_time = self.get_argument('blind_down_time')
                blind_back_time = self.get_argument('blind_back_time')
                max_sun_alt_shade = self.get_argument('max_sun_alt_shade')
                blind_afternoon_time = self.get_argument('blind_afternoon_time')
                max_sun_alt_open = self.get_argument('max_sun_alt_open')
                blind_open_time = self.get_argument('blind_open_time')

                rospy.set_param('/blind/'+id+"/mode", mode)
                #rospy.set_param('/blind/'+id+"/close_min_lum", close_min_lum)
                #rospy.set_param('/blind/'+id+"/close_min_temp", close_min_temp)
                rospy.set_param('/blind/'+id+"/blind_down_time", blind_down_time)
                rospy.set_param('/blind/'+id+"/blind_back_time", blind_back_time)
                rospy.set_param('/blind/'+id+"/max_sun_alt_shade", max_sun_alt_shade)
                rospy.set_param('/blind/'+id+"/blind_afternoon_time", blind_afternoon_time)
                rospy.set_param('/blind/'+id+"/max_sun_alt_open", max_sun_alt_open)
                rospy.set_param('/blind/'+id+"/blind_open_time", blind_open_time)

            try:
                os.system("rosparam dump /home/odroid/rosws/parameters.yaml")
            except Exception, e:
                raise e

        elif address[0] == 'blind':
            blind_id = address[1]
            blind_action = address[2]
            print "*********************************"
            print blind_action, blind_id
            print "################################"
            if blind_action == 'open' or blind_action == 'close':
                rospy.set_param('/blind/'+blind_id+"/status", blind_action)
            elif 'rotate_' in blind_action:
                value = rospy.get_param('/blind/'+blind_id+"/rotate")
                if blind_action == 'rotate_up':
                    rospy.set_param('/blind/'+blind_id+"/rotate", value + 100)
                elif blind_action == 'rotate_down':
                    rospy.set_param('/blind/'+blind_id+"/rotate", value - 100)


        else:
            print "NEZNAMY PARAMETR"
            print "---------------"
            #self.render("www/layout/dash/observatory.html", title = "AROM control center | observatory", leftmenu = leftmenu, actual = 'observatory', _sql=_sql)
            self.finish("loading...")


class bootstrap(web.RequestHandler):
    #@tornado.web.asynchronous
    def get(self, arg=None, path = None):
        try:
            print "Bootstrap page"
            print "-----------------"
            devices = get_devices()
            #print arg, path, devices
            driver = None
            properties = None

            try:
                #driver = eval(devices.data)[arg]
                #service = rospy.ServiceProxy(eval(devices.data)[arg]['service'], windowblind.srv.DriverControl)
                #properties = eval(service(name = 'advGetSetting', type = 'function', data = '', validate = '', check = '', done = True).data)
                #print properties
                pass

            except Exception, e:
                rospy.logerr(e)

            self.render("www/layout/dash/bootstrap.html", _sql=_sql, devices = devices, blinds = rospy.get_param('/blind'))
        except Exception, e:
            rospy.logerr(e)
            self.finish("Error v bot_set")

class bootstrap_setting(web.RequestHandler):
    def get(self):
        try:
            self.render("www/layout/dash/bootstrap_setting.html", _sql=_sql, devices = get_devices(), blinds = rospy.get_param('/blind'))
        except Exception, e:
            rospy.logerr(e)
            self.finish("Error v bot_set")

class node(web.RequestHandler):
    def get(self, arg = None):
        if not self.get_cookie("user"):
            devices = get_devices()
            driver = None
            properties = None

            try:
                driver = eval(devices.data)[arg]
                service = rospy.ServiceProxy(eval(devices.data)[arg]['service'], windowblind.srv.DriverControl)
                properties = eval(service(name = 'advGetSetting', type = 'function', data = '', validate = '', check = '', done = True).data)
                print properties

            except Exception, e:
                rospy.logerr(e)

            self.render("/home/odroid/rosws/src/windowblind/web/www/layout/dash/node_setting_public.html", arg = arg, driver = driver, properties = properties, blinds = rospy.get_param('/blind'))


        else:
            devices = get_devices()
            driver = None
            properties = None

            try:
                driver = eval(devices.data)[arg]
                service = rospy.ServiceProxy(eval(devices.data)[arg]['service'], windowblind.srv.DriverControl)
                properties = eval(service(name = 'advGetSetting', type = 'function', data = '', validate = '', check = '', done = True).data)
                print properties

            except Exception, e:
                rospy.logerr(e)

            self.render("/home/odroid/rosws/src/windowblind/web/www/layout/dash/node_setting.html", arg = arg, driver = driver, properties = properties, blinds = rospy.get_param('/blind'))

class Meteo(web.RequestHandler):
    def get(self, arg = None):
        if arg == None:
            #print arg
            self.finish('meteo meteo stránka :) :' + repr(arg))
        else:
            self.finish('stranka pro parametry :' + repr(arg))


class download(web.RequestHandler):
    def get(self, arg = None):
        if arg == None:
            #print arg
            self.finish('Download page :) :' + repr(arg))
        else:
            self.finish('stranka pro parametry :' + repr(arg))

class LoginHandler(BaseHandler):
    def get(self):
        self.write('<html><body><form action="/login" method="post">'
                   'Name: <input type="text" name="name"><br>'
                   'Pass: <input type="password" name="pass"><br>'
                   '<input type="submit" value="Sign in">'
                   '</form></body></html>')
    
    def post(self):
        if self.get_argument("name") == 'blind' and self.get_argument("pass") == 'blind':
            self.set_secure_cookie("user", 'Admin')
            self.redirect("/")
        else:
            self.redirect("/login")

class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("user")
        self.redirect("/")
        

app = web.Application([
        (r'/', bootstrap),
        (r'/node', node),
        (r'/node/(.*)', node),
        (r'/api/(.*)', BlindApi),
        (r'/meteo', Meteo),
        (r'/meteo/(.*)', Meteo),
        (r'/download/(.*)', tornado.web.StaticFileHandler,{"path": '/home/odroid/rosws/' }),
        #(r'/', bootstrap),
        #(r'/setting', bootstrap_setting),
        #(r'/api/(.*)', DriverPage),
        #(r'/(.*)', bootstrap),
       
        (r'/(favicon.ico)', web.StaticFileHandler, {'path': '/home/odroid/rosws/src/windowblind/web/www/media/favicon.ico'}),
        (r'/fonts/(.*)', tornado.web.StaticFileHandler,{"path": '/home/odroid/rosws/src/windowblind/web/www/fonts/' }),
        (r"/lib/(.*)", tornado.web.StaticFileHandler,{"path": '/home/odroid/rosws/src/windowblind/web/www/lib/' }),
        (r"/(.*\.png)", tornado.web.StaticFileHandler,{"path": '/home/odroid/rosws/src/windowblind/web/www/media/' }),
        (r"/(.*\.jpg)", tornado.web.StaticFileHandler,{"path": '/home/odroid/rosws/src/windowblind/web/www/media/' }),
        (r"/(.*\.ogg)", tornado.web.StaticFileHandler,{"path": '/home/odroid/rosws/src/windowblind/web/www/media/' }),
        (r"/(.*\.wav)", tornado.web.StaticFileHandler,{"path": '/home/odroid/rosws/src/windowblind/web/www/media/' }),
        (r"/(.*\.woff2)", tornado.web.StaticFileHandler,{"path": '/home/odroid/rosws/src/windowblind/web/www/fonts/' }),
        (r"/(.*\.css)", tornado.web.StaticFileHandler,{"path": '/home/odroid/rosws/src/windowblind/web/www/css/' }),
        (r"/(.*\.wav)", tornado.web.StaticFileHandler,{"path": '/home/odroid/rosws/src/windowblind/web/www/wav/' }),
        (r"/(.*\.json)", tornado.web.StaticFileHandler,{"path": '/home/odroid/rosws/src/windowblind/web/www/json/' }),
        (r"/(.*\.js)", tornado.web.StaticFileHandler,{"path": '/home/odroid/rosws/src/windowblind/web/www/js/' }),
       #(r"/static/(.*)", web.StaticFileHandler, {"path": "/var/www"}),
        (r"/login", LoginHandler),
        (r"/logout", LogoutHandler),
        (r"/(.*)", Overview),
    ],
    cookie_secret="IrehaxnWrArwyrcfvQvixnAnFirgr",
    debug=True,
    autoreload=True
    )

def main():
    app.listen(5252)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
