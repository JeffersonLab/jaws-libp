import os
import sys
import argparse

from PyQt5 import QtCore, QtGui, QtWidgets

from AlarmThread import *
from ModelView import *
from Filters import *
from PrefDialog import *
from OverrideDialog import *
from utils import *

#Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument('-test',help="Run in debug mode",action='store_true')
args = parser.parse_args()

SetTest(args.test)
      
#Parent toolbar. There are common actions for children.
#Specific actions are added by them
class ToolBar(QtWidgets.QToolBar) :
   def __init__(self,parent,*args,**kwargs) :
      super(ToolBar,self).__init__(*args,**kwargs)
      
      self.parent = parent      
      self.actionlist = []
      self.addActions()
   
   #Add the common actions   
   def addActions(self) :
      #Display user preferences
      prefaction = PrefAction(self).addAction()
      
      #Actions added to the actionlist are subject to configuration
      propaction = PropertyAction(self).addAction()
      self.actionlist.append(propaction)
      
      removefilter = RemoveFilterAction(self).addAction()
      self.removefilter = removefilter
      
   
   #Access to the Remove Filter action button
   def getRemoveFilterAction(self) :
      return(self.removefilter)
         
   #Configure the tool bar when necessary
   def configureToolBar(self) :
      for action in self.actionlist :               
         action.configToolBarAction()
      

#NOT IMPLEMENTED YET
class JAWSMessenger(QtWidgets.QWidget) :
   def __init__(self,parent=None,*args,**kwargs) :
      super(JAWSMessenger,self).__init__(parent,*args,**kwargs)
      
      layout = QtWidgets.QHBoxLayout()
      self.timestamp = QtWidgets.QLabel()
      self.timestamp.setFixedWidth(10)
      layout.addWidget(self.timestamp) 
      
      self.message = QtWidgets.QLabel()
      layout.addWidget(self.message)
      
      self.setLayout(layout)
   
   def setMessage(self,timestamp,message) :
      self.timestamp.setText(timestamp)
      self.message.setText(message)   
      
      
#only one widget for a main window
class JAWSManager(QtWidgets.QMainWindow) :
   def __init__(self,title,type,*args,**kwargs) :
      super(JAWSManager,self).__init__(*args,**kwargs)
      
      setManager(self)
         
      #Instantiate Manager members
      self.type = type  #Manager type
      self.data = []    #alarm data
      self.filters = [] #available alarm filters
      
      self.consumer_dict = {}
      self.consumers = []
      self.overridedialog = None   #dialog displaying suppression options
      self.prefdialog = None    #dialog displaying preferences
      self.removefilter = None  #Removes all filters.Associated with the tool bar
      
      self.propdialogs = {}
      self.managerprefs = self.readPrefs() #Read user preferences.
      
      #Begin to configure the main window     
      self.setWindowTitle(title)
          
      #Create the pieces and parts of the modelview and tableview
      self.createModelAndTable()
      
      self.toolbar = self.createToolBar()  
      self.addToolBar(self.toolbar)
       
      #Put the table in the main widget's layout.
      #Need to have a layout for its size hint.
      layout = QtWidgets.QGridLayout()
      
      menubar = self.createMenuBar()
      layout.addWidget(menubar)      
      layout.addWidget(self.tableview)
      
    #  self.messenger = JAWSMessenger()      
     # layout.addWidget(self.messenger)
      ############   NEEDS TO BE EXERCISED BEFORE REMOVAL 
      #Total misnomer. This command grows and shrinks the main window
      #when the table rows are added or removed. Also allows for the
      #size grip to still be used by the user.
      layout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize);
         
      #The actual widget. 
      widget = QtWidgets.QWidget()
      widget.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
         QtWidgets.QSizePolicy.MinimumExpanding)
      widget.setLayout(layout)
      
      #We will use the widget later to resize the MainWindow
      self.widget = widget
      
        
      #Show the results
      self.setCentralWidget(widget)
      self.show()
      
 
      #Initial configuration based on prefs and alarm
      #status
      self.initConfig()
      
      #Initialize
      self.processor = self.createProcessor()
      
      #Start the worker threads to monitor for messages
      self.startWorkers()
      
      #Initialize the size of the main gui
      self.setSize()
   
   def setMessage(self,timestamp,message) :
      self.messenger.setMessage(timestamp,message)
      
         
   ### THE FOLLOWING METHODS DEAL WITH THREADING
   
   #Create and start the worker.
   def startWorkers(self) :
      
      #Create a thread for each topic
      topics = self.processor.get_topics()
      
      self.threadpool = QThreadPool()  
      self.threadpool.setMaxThreadCount(len(topics) + 1)
         
      self.workerthreads = {}
      for topic in topics :
         worker = JAWSWorker(self.createConsumer,topic)
         self.workerthreads[topic] = worker
         worker.signals.progress.connect(self.updateAlarms)
        
         self.threadpool.start(worker)
         self.workerthreads[topic] = worker
         

   #Create a consumer for the topic  
   def createConsumer(self,topic) :
      
      if (topic == 'active-alarms') :
         consumer = ActiveAlarmsConsumer(self.initMessages,
            self.updateMessages,self.type)
      elif (topic == 'alarm-state') :
         consumer = AlarmStateConsumer(self.initMessages,
            self.updateMessages,self.type)
      elif (topic == 'registered-alarms') :
         consumer = RegisteredAlarmsConsumer(self.initMessages,
            self.updateMessages,self.type)
      else :
         #The JAWSConsumer includes the event table, which will be
         #the thread.
         consumer = JAWSConsumer(topic,self.initMessages,
            self.updateMessages,self.type)
      
      self.consumers.append(consumer)
      #Start the consumer 
      consumer.start()
      
   #Initial messages (this is in the jawsconsumer thread)
   def initMessages(self,msglist) :      
      
      #Process each alarm 
      for msg in msglist.values() :        
         topic = get_msg_topic(msg)    
         worker = self.workerthreads[topic]
         worker.signals.progress.emit(msg)
         
   
   #Called when there is a new message (jaws consumer thread)
   def updateMessages(self,msg) :    
      topic = get_msg_topic(msg)      
      worker = self.workerthreads[topic]
      worker.signals.progress.emit(msg)
   
   #Back to the main GUI thread.
   ##### SOME OF THIS MAY BE PUSHED TO THE INHERITED MANAGER
   def updateAlarms(self,msg) :      
      alarm = self.processor.process_alarm(msg)
      if (msg.topic() == "registered-alarms") :
         self.configureOverrideDialog()
      if (alarm != None) :
         state = alarm.get_state(name=True)
         
         if (state != None) :
            state = state.lower()
            if (state == "active" or "latched" in state) :
               getModel().addAlarm(alarm)
            elif (re.search("normal",state) != None) :
               getModel().removeAlarm(alarm)
            elif (re.search("shelved",state) != None) :
               getModel().removeAlarm(alarm)
            else :
               
               getModel().removeAlarm(alarm)
         else :
            getModel().removeAlarm(alarm)
           
   
   #Close the GUI gracefully (MainWindow function) 
   #closeEvent != CloseEvent
   def closeEvent(self, event=QtGui.QCloseEvent()) :
      
      #Close down the consumers nicely
      if (self.consumers != None) :        
         for consumer in self.consumers :        
            consumer.stop()
      sys.exit(0)
   
   
   #Create the table, model, and proxymodel that will
   #display and organize the alarm data
   def createModelAndTable(self) :
   
      ##### Using a proxymodel allows us to easily sort and filter
      proxymodel = self.getProxyModel()      
      self.proxymodel = proxymodel
      
      #Create the TableView widget that will display model
      self.tableview = self.createTableView()
      
      #Create the alarmmodel that will be displayed in the table
      self.modelview = self.createModelView()
      
      #Assign the model to the table
      self.tableview.setModel(proxymodel)
      self.tableview.setSortingEnabled(True)  
       
      #Have to connect AFTER model has been set in the tableview
      #If a row is selected, the tool bar configuration may change
      self.tableview.selectionModel().selectionChanged.connect(
         self.tableview.rowSelected)
      
      self.proxymodel.setSourceModel(self.modelview)
      
      #Make the model and the table available      
      setModel(self.modelview)
      setTable(self.tableview)
      setProxy(self.proxymodel)
   
   #Managers use the same proxymodel class
   def getProxyModel(self) :
      proxymodel = ProxyModel()     
      return(proxymodel)
   
   def getProcessor(self) :
      return(self.processor)
      
   #Configure based on the initial set of messages
   def initConfig(self) :
      self.applyPrefs()
      self.configureColumns()
      self.configureToolBar()
   
   #Configure the column width.
   #Some columns have a width assigned  
   def configureColumns(self) :
      getModel().configureColumns()
    
   #Configure the tool bar.   
   def configureToolBar(self) :
      self.getToolBar().configureToolBar()
   
   def configureProperties(self,alarm) :
      if (alarm.get_name() in self.propdialogs) :
         dialog = self.propdialogs[alarm.get_name()]
         dialog.configureProperties()
   
   def configureOverrideDialog(self) :
      if (self.overridedialog != None) :
         self.overridedialog.reset()
         
   #Access to the Manager's toolbar  
   def getToolBar(self) :
      return(self.toolbar)
      
   #Access the RemoveFilter for configuration  
   def getRemoveFilterAction(self) :
      return(self.getToolBar().getRemoveFilterAction())
   
   #Access the manager's set of filters.      
   def getFilters(self) :      
      return(self.filters)
   
   
   ### The following deals with accessing and applying
   #   user preferences.
   
   #Access this manager's preference configuration   
   def getPrefs(self) :
      return(self.managerprefs)

   #Create the preference file name   
   def getPrefFile(self) :
      user = getUser()
      manager = self.name
      filename = "." + user + "-jaws-" + manager
      return(filename)
   
   #Read preference file.
   #Preferences contain initial configuration information 
   #such as hidden/shown table columns
   def readPrefs(self) :
      prefs = {}
      filename = self.getPrefFile()
      
      if (os.path.exists(filename)) :        
         #Preference file is written as a dictionary.
         #The "eval" turns the string back into a dictionary
         line = open(filename,'r').read()
         if (len(line) > 0) :
            prefs = eval(line)
      return(prefs)
   
   #Save the user preferences.
   def savePrefs(self) :
      filename = self.getPrefFile()
      if (os.path.exists(filename)) :
         os.remove(filename)
      #Write the preference dictionary to the file.
      prefs = self.managerprefs
      with open(filename,"a+") as file :
        file.write(str(prefs))
      file.close()
   
   #Apply preferences if applicable
   def applyPrefs(self) :
      prefs = self.getPrefs()
      if (prefs == None) :
         return
      
      if ("display" in prefs) :
         getModel().applyChanges(prefs['display']['show'])
         
      if ("sort" in prefs) :
         sortcolumn = prefs['sort']['column']
         sortorder = prefs['sort']['order']
      else :
         (sortcolumn,sortorder) = getTable().GetDefaultSort()
      getTable().sortByColumn(sortcolumn,sortorder)
   
   ### The following deal with the manager's filters.
   
   #Create the filters for the manager.
   def makeFilters(self) :
      #Not all columns have filters. 
      columns = self.columns
      for col in columns :          
         if ("filter" in columns[col]) :
            filtertype = columns[col]['filter']            
            filter = filtertype()           
            self.filters.append(filter)
      
      self.initFilters()
  
   #Handler initial filter values (from prefs file) a little 
   #differently
   def initFilters(self) :
      
      prefs = self.getPrefs()      
      if (not 'filters' in prefs) :
         prefs['filters'] = {}
         
      #if (prefs != None and "filters" in prefs) :
      for filter in self.filters :
         name = filter.getName()
         settings = filter.getCurrentSettings()
         if (name in prefs['filters']) :
            settings = prefs['filters'][name]
         
         filter.setSettings(settings)               
         filter.setHeader()
         
   #Create the preference dialog
   def createPrefDialog(self) :
      if (self.prefdialog == None) :
         self.prefdialog = PrefDialog()
      return(self.prefdialog)
   
   #Access the preference dialog
   def getPrefDialog(self) :
      return(self.prefdialog)
        
   #Create a dialog for overriding an alarm. Common to children
   def createOverrideDialog(self,selectedalarms=None) :
      
      if (self.overridedialog == None) :
         self.overridedialog = OverrideDialog(selectedalarms)
      self.overridedialog.setSelection(selectedalarms)
      return(self.overridedialog)   

   #Adjust the size of the main gui when alarms are added/removed
   def setSize(self) :
      self.widget.adjustSize()
      self.adjustSize() 
