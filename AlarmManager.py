"""
.. module:: AlarmManager
   :synopsis : JAWSManager that displays active alarms
.. moduleauthor:: Michele Joyce <erb@jlab.org>
"""
from signal import signal, SIGINT
from sys import exit

from JAWSManager import *
from jlab_jaws_helper.JAWSProcessor import *

from AlarmProcessor import *
from TableView import *
"""
Column definitions for an AlarmManager
"""
COLUMNS = {
     'type' :  {'size' : 75, 'filter' : TypeFilter,'settings' : None},
     'priority' : {'size' : 175, 'filter' : PriorityFilter,'settings' : None},
     'status' : {'size': 75, 'filter' : StatusFilter,'settings' : None},
     'name' : {'size' : 200},
     'timestamp': {'size': 150, 'settings' : None, 'sortorder': 1},  
     'location' : {'filter' : LocationFilter,'settings' : None},
     'category' : {'filter' : CategoryFilter, 'settings' : None}
}
 
class AlarmManager(JAWSManager) :
   """ A JAWSManager to display active alarms
   """
   def __init__(self,*args,**kwargs) :
         
      self.columns = COLUMNS
      self.name = "alarmmanager"  
      
      super(AlarmManager,self).__init__("JAWS - Active Alarm Manager",self.name,
         *args,**kwargs)
      
      
      #Apply filters if presetn
      if (len(self.filters) == 0) :
         self.makeFilters()
     
   def createToolBar(self) :
      """ AlarmManager toolbar
      """
      toolbar = AlarmToolBar(self)
      return(toolbar)
   
   def createMenuBar(self) :
      """ AlarmManager menubar
      """
      menubar = AlarmMenuBar(self)
      return(menubar)
 
   #The Alarm Table
   def createTableView(self) :
      """ Display table
      """
      tableview = AlarmTable()      
      return(tableview)
   
   #The Alarm Model
   def createModelView(self) :
      """ Alarm model
      """
      modelview = AlarmModel(self.data)      
      return(modelview)

   #AlarmProcessor inherits from Processor
   def createProcessor(self) :
      """ Monitors applicable topics and processes them
      """
      processor = AlarmProcessor()
      return(processor)
   
   def createPropertyDialog(self,alarm) :
      """ Create a property dialog for an active alarm  
          :param alarm: alarm to display
          :type alarm : JAWSALARM
      """
      
      name = alarm.get_name()
      if (name in self.propdialogs) :
         propertydialog = self.propdialogs[name]
      else :
         
         propertydialog = AlarmPropertyDialog(alarm,self)
         self.propdialogs[name] = propertydialog
         
      return(propertydialog)
   
   #The Alarm/Shelf Preference Dialogs have different spacing and sizeHint 
   #variables.
   #PROBABLY SHOULD BE KEPT WITH PREF DIALOG...
   def prefSpacing(self) :
      return(2)
   def prefMultiplier(self) :
      return(30)
        
   

#The AlarmManager specific toolbar. 
#Slightly different from the OverrideManager
class AlarmToolBar(ToolBar) :
   def __init__(self,parent,*args,**kwargs) :
      super(AlarmToolBar,self).__init__(parent,*args,**kwargs)
   
   #Create the toolbar actions
   def addActions(self) :
      super().addActions()
      
      ackaction = AckAction(self).addAction()
      self.actionlist.append(ackaction)
      
     
      #Add access to overrides to the AlarmManager toolbar
      overrideaction = OverrideAction(self).addAction()
      self.actionlist.append(overrideaction)
      
      
   
class AlarmMenuBar(QtWidgets.QMenuBar) :
   """ Menubar specific to the AlarmManager
   """
   def __init__(self,parent,*args,**kwargs) :
      """ Create the menu bar
      """
      super(AlarmMenuBar,self).__init__(parent,*args,**kwargs)                
      filemenu = self.addMenu("File")
      
      prefsaction = PrefAction(self)
      filemenu.addAction(prefsaction)
      
     # overrideaction = QAction("Launch Override Manager",self)
     # overrideaction.triggered.connect(self.LaunchShelfManager)
     # filemenu.addAction(shelfaction)
      
      exitaction = QAction("Quit",self)
      exitaction.triggered.connect(parent.closeEvent)
      filemenu.addAction(exitaction)
   
  
   def LaunchShelfManager(self,event) :
      """ User can launch an instance of the ShelfManager
      """
      command = "python3 " + SOURCEDIR + "ShelfManager.py &"
      os.system(command)
 
      
def handler(signal_received,frame) :
   print("FRAME:",frame)
   print('SIGINT or CTRL-C detected.Exiting gracefully')
   

   
app = QtWidgets.QApplication(sys.argv)
window = AlarmManager()
app.exec()
