
import datetime
import tempfile  

import re 
import getpass
import pytz
import time
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QIcon, QPixmap, QImage, QFont, QColor
from jlab_jaws.avro.subject_schemas.entities import *

#from jlab_jaws_helper import JAWSConnection

DEPLOY = "ops"

TEST = False
MANAGER = None

PROCESSOR = None

MESSENGER = None
MODEL = None
TABLE = None
PROXY = None

REGISTEREDALARMS = {}
ACTIVEALARMS = {}
SHELVEDALARMS = {}
PRODUCERS = {}

PROPERTIES = {}
   

ALARMS = {}

BIGBOLD = "-*-helvetica-medium-r-bold-*-16-*-*-*-*-*-*-*"
SMALLBOLD =  "-*-helvetica-medium-r-bold-*-12-*-*-*-*-*-*-*"
SMALL = "-*-helvetica-medium-r-medium-*-12-*-*-*-*-*-*-*"

IMAGEPATH = "./"

ALARMSTATUS = {
   "MAJOR"     : {
      "rank" : 3, "color" : 'red',    "image" : None, "shelved" : None},
   "MINOR"     : {
      "rank" : 1 , "color" : 'yellow', "image" : None, "shelved" : None},
   "ALARM"  : {
      "rank" : 2, "color" : 'red', "image" : None, "shelved" : None},
   "ACK"       : {
      "rank" : 2 ,"color" : 'white' , "image" : None} ,
   "NO_ALARM"  : {
      "rank" : 0, "color" : 'white' , "image" : None, "shelved" : None},
}

QUICKDURATIONS = {
   "1" : {
      "text" : "5 seconds", "seconds" : 5},
   "2" : {
      "text" : "1 minute", "seconds" : 60},
   "3" : {
      "text" : "1 hour", "seconds": 3600},
   "4" : {
      "text" : "1 day", "seconds": 86400}
}

SOURCEDIR = "./"
 
def getUser() :
   return(getpass.getuser())

####
def CheckIfProcessRunning(name) :
   return False
   for proc in psutil.process_iter() :
      try :
         print(name.lower(), proc.name().lower())
         if (name.lower() in proc.name().lower()) : return True
         
      except :
         pass
      return False

def MakeBold(label) :
   font = QtGui.QFont()
   font.setBold(True)
   label.setFont(font)
   
####### CREATE PROPERTY ROWS #####

def setMessage(timestamp,message) :
   getManager().setMessage(timestamp,message)


def MakeLabel(text,bold=True) :
   label = QtWidgets.QLabel(text)
   if (bold) :
      MakeBold(label)
   return(label)

def FormatTime(timestamp) :
   formatted = None
   if (timestamp != None) :
      formatted =  timestamp.strftime("%Y-%m-%d %H:%M:%S")
   
   return(formatted)
 
def confirmAlarms(alarmlist,which="Shelve") :
   alarmnames = []
   for alarm in alarmlist :
      alarmname = alarm.get_name()
      alarmnames.append(alarmname)
   
   
   message = which + " the following alarms?\n\n" + "\n".join(alarmnames)
   msgBox = QtWidgets.QMessageBox()
   msgBox.setIcon(QtWidgets.QMessageBox.Question)
   msgBox.setText(message)
   msgBox.setStandardButtons(QtWidgets.QMessageBox.Yes|
      QtWidgets.QMessageBox.Cancel)
   reply = msgBox.exec()
      
   confirm = False
   if (reply == QtWidgets.QMessageBox.Yes) :
      confirm = True
         
   return(confirm)
      
   
def GetAlarmType(msgtype) :
   
   type = "StreamRuleAlarm"
   if ("EPICS" in msgtype) :
      type = "DirectCAAlarm"
   
   return(type)
   
def ConvertTimeStamp(seconds) :
   #Work in utc time, then convert to local time zone.
   ts = datetime.fromtimestamp(seconds//1000)
   utc_ts = pytz.utc.localize(ts)
      
   #Finally convert to EST.
   est_ts = utc_ts.astimezone(pytz.timezone("America/New_York"))
   return(est_ts)

#def GetRank(status) :   
 #  status = TranslateACK(status)   
  # if (status == None) :
   #   return(None)
   #return(ALARMSTATUS[status]['rank'])

#Little utility so that it's not necessary to keep track
#of the rows in case more/less are needed.
def nextRow(widget) :
   row = widget.row
   if (row != None) :
      row = row + 1
   else :
      row = 0
   widget.row = row
   return(row)

def raiseAndResetDialog(dialog) :   
   dialog.show()
   dialog.activateWindow()
   dialog.raise_()
   dialog.reset()


def GetStatusImage(status) :
   
   status = TranslateACK(status)
   
   image = None
   color = GetStatusColor(status)
   
   if (color != None) :
      if (ALARMSTATUS[status]['image'] == None) :
         filename = IMAGEPATH + color + "-big.png"
 
         image = QImage(filename)
         pixmap = QPixmap.fromImage(image)
         
         ALARMSTATUS[status]['image'] = pixmap
      image = ALARMSTATUS[status]['image']
   return(image)

 
def setProxy(proxy) :
   global PROXY
   PROXY = proxy

def getProxy() :
   return(PROXY)
        
def setModel(model) :
   global MODEL
   MODEL = model

def getModel() :
   return(MODEL)

def TranslateACK(status) :
   return(status)
   ack = status
   if (status != None) :
      match = re.search("(.*)_ACK",status)
      if (match != None) :
         ack = match.group(1)
         if (ack == "NO") :
            ack = status
   return(ack)

def GetQtColor(status) :
   color = GetStatusColor(status)
   if (color != None) :
      return(QColor(color))
      
   return None

def GetStatusColor(status) :
   status = TranslateACK(status)
      
   color = None
   if (status in ALARMSTATUS.keys()) :
      color = ALARMSTATUS[status]['color']
   return(color)

def SetConsumer(consumer) :
   global CONSUMER
   CONSUMER = consumer

   
def SetProducer(producer,topic) :
   global PRODUCERS
   PRODUCERS[topic] = producer

def GetProducer(topic) :
   producer = None
   if (topic in PRODUCERS) :
      producer = PRODUCERS[topic]
      
   return(producer)
   

#Add and access registered alarms  


def AddShelvedAlarm(alarm) :
   SHELVEDALARMS[alarm.get_name()] = alarm
   
def FindShelvedAlarm(alarmname) :
   found = None
   if (alarmname in SHELVEDALARMS) :
      found = SHELVEDALARMS[alarmname]
   return(found)
   
#Add and access active alarms
def AddActiveAlarm(alarm) :
   
   ACTIVEALARMS[alarm.get_name()] = alarm


     
def FindActiveAlarm(alarmname) :
   found = None
   if (alarmname in ACTIVEALARMS) :
      found = ACTIVEALARMS[alarmname]
   return(found)

def FindAlarm(alarmname) :
   found = FindActiveAlarm(alarmname)
   if (found == None) :
      found = FindShelvedAlarm(alarmname)

   return(found)

def SetAlarmList(alarmlist) :
   global ALARMLIST
   ALARMLIST = alarmlist

def getAlarmNames() :
   names = []
   for alarm in getModel().data :
      names.append(alarm.get_name())
   return(names)
   
def GetAlarmList() :
   return(getModel().data)
   
def SetShelvedList(shelvedlist) :
   global SHELVEDLIST
   SHELVEDLIST = shelvedlist

def GetShelvedList() :
   return(SHELVEDLIST)

def SetActiveList(activelist) :
   global ACTIVELIST
   ACTIVELIST = activelist

def GetActiveList() :
   return(ACTIVELIST) 
   
#Command-line option -deploy. Set to use throughout.      
def SetDeployment(deploy) :
   global DEPLOY
   DEPLOY = deploy

#Access command-line -deploy option
def GetDeployment() :
   return(DEPLOY)

#Command-line option -test. Set to use throughout   
def SetTest(test) :
   global TEST
   TEST = test

#Access command-line -test option
def GetTest() :
   return(TEST)

def setManager(manager) :
   global MANAGER
   MANAGER = manager

#Access to the main gui
def getManager() :
   return(MANAGER)   

def WhichManager() :
   return(MANAGER.manager)
   
def setTable(table) :
   global TABLE
   TABLE = table

def getTable() :
   return(TABLE)


#Create the timestamp for the datafile, using the current time.   
def TimeStamp() :
   timestamp = datetime.datetime.now()
  
   return(timestamp.strftime("%s"))

