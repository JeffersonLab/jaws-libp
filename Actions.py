""" 
.. module:: Actions
   :synopsis : Create QActions 
.. moduleauthor::Michele Joyce <erb@jlab.org>
"""

from utils import *
from jlab_jaws_helper.JAWSConnection import *

#Define the Actions class
#Actions can be shared by the tool bars and context menus
class Action(QtWidgets.QAction) :
   """ Define the Actions Class. Actions can be shared by the toolbars and 
       contextmenus
   """
   def __init__(self,parent,*args,**kwargs) :
      super(Action,self).__init__(parent,*args,**kwargs)
      """ Create an action
         
         Args:
            parent (widget) : parent widget
      
      """    
      #Inherited action passes in configuration information
      self.parent = parent            
      
      if (self.icon != None) :
         self.setIcon(self.icon)              
      
      if (self.text != None) :
         self.setIconText(self.text)      
      if (self.tip != None) :
         self.setToolTip(self.tip)
      
      self.triggered.connect(self.performAction)
      
 
   def configToolBarAction(self) :
      """  Configure the toolbar actions. 
           This subroutine can be overwritten by inherited actions.
      """
      pass
   
   def getSelectedAlarms(self) :
      """ 
         Get the list of alarms that have been selected on the table
         Returns:
            list of JAWSAlarms
      """      
      return(getTable().getSelectedAlarms())
   
   def getSelectedAlarm(self) :
      """ 
         Get the single selected alarm 
         Returns:
            JAWSAlarm
      """      
      return(getTable().getSelectedAlarm())
            
   def addAction(self) :
      """ 
         Add an action. 
         Action may be added to a contextmenu, or toolbar     
      """    

      #If this isn't a menu, add it to the parent and return
      if (not isinstance(self.parent,QtWidgets.QMenu)) :
         self.parent.addAction(self)
         return(self)
      
      #If it is a context menu invoked when alarm(s) are selected
      #need to determine if 1. The action is valid 2. The text of the action
      valid = True
      valid = self.actionValid()
      
      #Only add to the menu if valid
      if (valid) :
         text = self.getText()
         self.parent.addAction(self)
         self.setText(text)
      return(self)
      
   def actionValid(self) :
      """ 
         Default validity check. Valid if at least one alarm is selected.
         NOTE: Can be overridden by children
         
         Returns: (bool) 
            valid/invalid 
      """
      valid = True
      if (len(self.getSelectedAlarms()) == 0) :
         valid = False
      return(valid)
   
   def performAction(self) :      
      """ Children must implement
      """
      pass
      
   def getText(self) :
      """ 
         Default text depends on the action's "actionword" and
         the number of alarms selected.
         NOTE: Can be overridden by children
         
         Returns :
            text for action

      """
      actionword = self.actionword
      text = actionword 
      return(text)



class TitleAction(Action) :
   """ Dummy action used to control title of contextmenu
   """
   def __init__(self,parent,*args,**kwargs) :
      """
         Parameters:
            parent (menu) : parent menu          
      """     
      
      self.icon = None
      self.text = None
      self.tip = None
      
      super(TitleAction,self).__init__(parent,*args,**kwargs)
   
   def getText(self) :
      """ Text dependent on number of alarms that have been selected in the table
          Returns:
            title for action
      """
      title = "Selected Alarms"
      alarms = getTable().getSelectedAlarms()
      if (len(alarms) == 1) :
         title = alarms[0].get_name()
      return(title)
  

class PrefAction(Action) :
   """ Display user preferences
       NOTE: This action is added to the toolbar as well as the file menu
   """
   
   def __init__(self,parent,*args,**kwargs) :
      """
         Create an instance
         Args:
            parent: QMenu or QToolbar 
      """
        
      self.icon = QtGui.QIcon("gear.png")
      self.text = "Preferences"
      self.tip = "Preferences"
      
      super(PrefAction,self).__init__(parent,*args,**kwargs)
   
   #Invoke the preferences dialog.
   def performAction(self) :
      """ Display the user preferences dialog """           
      dialog = getManager().createPrefDialog()
      raiseAndResetDialog(dialog)
 
 
class OverrideAction(Action) :
   """ Display override option dialog
   """
   def __init__(self,parent,text="Override Selected",*args,**kwargs) :
      """
         Create an instance
         Args:
            parent: QMenu or QToolbar 
      """
      self.icon = QtGui.QIcon("cross-circle.png")
      self.text = "Override Alarms"
      self.tip = "Override Alarms"
      
      self.actionword = "Override"
      super(OverrideAction,self).__init__(parent,*args,**kwargs)
   
   def configToolBarAction(self) :
      """  The action is only available,if at least one alarm is 
           being displayed
      """           
      if (self.actionValid()) :
         self.setEnabled(True)
      else :
         self.setEnabled(False)
   
   def actionValid(self) :
      """ 
         Valid if at least one alarm is displayed
         returns: valid/invalid 
      """
      valid = True ### TESTING
      if (getModel().rowCount(0) == 0) :
         valid = False
      return(valid)
   
   #Create/show the OverrideDialog
   def performAction(self,selectedalarms=None) :
      
      #Has a overridedialog already been created?
      dialog = getManager().createOverrideDialog(None)
 
      #pop
      raiseAndResetDialog(dialog)   
      
      #If called from the context menu, pre-populate the search box for the
      #dialog
      if (selectedalarms and len(selectedalarms) > 0) :
         dialog.setSelection(selectedalarms)   

      
      
class RemoveFilterAction(Action) :
   """
      For visual hint of filtered data, this toolbar button is checked 
      automatically if a filter on any column has been applied
      If the user DESELECTS the button, all column filters will be removed.  
      The button is disabled if there are no filters applied to the table
   """
   def __init__(self,parent=None,*args,**kwargs) :
      """
         Create an instance
         Args:
            parent: QToolbar 
      """
            
      self.icon = QtGui.QIcon("funnel--minus.png")
      self.text = "Remove Filters"
      self.tip = "Remove all Filters"
      self.parent = parent
      self.filters = getManager().getFilters()
      
      super(RemoveFilterAction,self).__init__(parent,*args,**kwargs)
      self.setCheckable(True)
   
 
   def setState(self) :
      """
         State of buttons depends on all filters.
         If a filter has been removed, need to check all other filters 
         to determine state
      """
      
      #Assume that there are no filters on the table
      filtered = self.getFilterState()
     
      self.setEnabled(filtered)
      self.setChecked(filtered)
      
      #The Preference Dialog (if has been created) should also be 
      #configured.
      prefdialog = getManager().getPrefDialog()
      if (prefdialog != None) :        
         prefdialog.configureDialog()
         
   def getFilterState(self) :
      """
         Are any filters applied?
         :returns boolean
      """      
      filtered = False          
      for filter in self.filters :
         #if one filter is applied, the manager is filtered
         if (filter.isFiltered()) :
            filtered = True
            break       
      return(filtered)
   
   def removeAllFilters(self) :
      """ Remove all of the filters """
      for filter in self.filters :
         filter.selectAll(True)
      self.setState()
               
   def performAction(self) :     
      """ Called when the Filter tool bar button is pushed """
      removefilters = not self.isChecked()
      if (removefilters) :
         self.removeAllFilters()
 
class PropertyAction(Action) :
   
   """ Display the properties of an alarm """
   
   def __init__(self,parent,text="Properties",*args,**kwargs) :
      """ 
         Create an instance
         
         Args:
            parent: QMenu or QToolbar
            text: string (default = "Properties")
     
      """
      #Define the action's configuration          
      self.icon = QtGui.QIcon("property-blue.png")
      self.text = "Properties"
      self.tip = "Alarm Properties"
      self.actionword = "Properties"
      #Now call the parent.
      super(PropertyAction,self).__init__(parent,*args,**kwargs)
   
  
   def configToolBarAction(self) :
      """  The action is only available, if ONE alarm is selected. """        
      alarmlist = self.getSelectedAlarms()
      self.setEnabled(True)
      
      if (len(alarmlist) == 1) :
         self.setEnabled(True)
      else :
         self.setEnabled(False)
   
   def performAction(self,alarmlist = None) :
      """ Show the alarm's property dialog """
      
      alarm = self.getSelectedAlarms()[0]
      dialog = getManager().createPropertyDialog(alarm)
      #pop
      raiseAndResetDialog(dialog)    
      
  
   def actionValid(self) :
      """ Action only valid if one, and only one alarm has been selected. 
          Returns:
            True/False
      """      
      valid = True
      num = len(self.getSelectedAlarms())
      if (num != 1) :
         valid = False
      return(valid)
   

class OneShotAction(Action) :
   """ OneShot override """
   
   def __init__(self,parent,text="One Shot Override",*args,**kwargs) :
      """ 
         Create an instance
         
         Args:
            parent: QMenu,QToolbar, or None
            text: string (default = "One Shot Override")
     
      """
  
      self.icon = QtGui.QIcon("hourglass--arrow.png")
      self.text = text
      self.tip = "OneShot"
      self.actionword = "OneShot Shelve"
      super(OneShotAction,self).__init__(parent,*args,**kwargs)
      
   
   def performAction(self,reason,comments=None,alarmlist=None) :                
      """ 
         One Shot Override
         Args:
            reason (enum)    : official reason for override
            comments (str)   : optional free form comments
            alarmlist (list) : optional list of alarms to override
      """
      if (reason == None) :
         reason = "Other"
      
      #Create an OverrideProducer to send message to overridden topic
      #Create an ackproducer too. Until state processor fixed to remove
      #latch if shelved
      oneshotproducer = OverrideProducer(getManager().type,'Shelved')
      ackproducer = OverrideProducer(getManager().type,'Latched')
      
      if (alarmlist == None) :
         alarmlist = self.getSelectedAlarms()
      
      #Send the messages for each alarm.
      for alarm in alarmlist :
         oneshotproducer.oneshot_message(alarm.get_name(),reason,comments)
         ackproducer.ack_message(alarm.get_name())

class DisableAction(Action) :
   """ Disabled override """
   
   def __init__(self,parent,text="Disable",*args,**kwargs) :
      """ 
         Create an instance       
         Args:
            parent: QMenu,QToolbar, or None
            text: string (default = "Disable")     
      """
      self.icon = QtGui.QIcon("cross-circle.png")
      self.text = text
      self.tip = "Disable"
      self.actionword = "Disable"
      super(DisableAction,self).__init__(parent,*args,**kwargs)
   
   def performAction(self,comments=None,alarmlist=None) : 
      """ 
         Disable Override
         Args:
            comments (str)   : optional free form comments
            alarmlist (list) : optional list of alarms to override
      """
      
      #Create an OverrideProducer to send message to overridden topic
      #Create an ackproducer too. Until state processor fixed to remove
      #latch if shelved
      disableproducer = OverrideProducer(getManager().type,"Disabled")
      ackproducer = OverrideProducer(getManager().type,'Latched')
      
      if (alarmlist == None) :
         alarmlist = self.getSelectedAlarms()
      
      if (not alarmlist) :
         return
      
      #Disable each alarm in the list.
      for alarm in alarmlist :
         disableproducer.disable_message(alarm.get_name(),comments)
         ackproducer.ack_message(alarm.get_name())

  
class TimedOverrideAction(Action) :
   """ Time override (Shelved) """
   
   def __init__(self,parent,seconds,text="Timed Shelving",*args,**kwargs) :
      """ 
         Create an instance       
         Args:
            parent: QMenu,QToolbar, or None
            text: string (default = "Timed Shelving")   
            seconds (int) : number of seconds to override
      """
      self.icon = QtGui.QIcon("alarm-clock--arrow.png")
      self.text = text
      self.tip = "Shelving"
      self.actionword = "Timed Shelving"
      
      self.expirationseconds = seconds     
      super(TimedOverrideAction,self).__init__(parent,*args,**kwargs)
   
   def performAction(self,reason,comments=None,alarmlist=None) : 
      """ 
         Timed override (Shelved)
         Args:
            reason           : official reason for override
            comments (str)   : optional free form comments
            alarmlist (list) : optional list of alarms to override
      """     
      shelfproducer = OverrideProducer(getManager().type,'Shelved')
      ackproducer = OverrideProducer(getManager().type,'Latched')
      
      
      if (alarmlist == None) :
         alarmlist = self.getSelectedAlarms()
      if (not alarmlist) :
         return
      
      for alarm in alarmlist :
         shelfproducer.shelve_message(alarm.get_name(),self.expirationseconds,
            reason,comments)        
         ackproducer.ack_message(alarm.get_name())

#Acknowledge Action      
class AckAction(Action) :
   """ Acknowledge alarms """
   
   def __init__(self,parent,text="Acknowledge Alarms",*args,**kwargs) :
      """ 
         Create an instance       
         Args:
            parent: QMenu,QToolbar, or None
            text: string (default = "Ackowledge Alarms")            
      """ 
      self.icon = QtGui.QIcon("tick-circle-frame.png")
      self.text = text
      self.tip = "Acknowledge"
      
      self.actionword = "Ack"
      super(AckAction,self).__init__(parent,*args,**kwargs)
     
   
   def getAlarmsToBeAcknowledged(self) :
      """ 
         Determine which selected alarms need to be acknowledged 
         Returns:
            list of alarms to be acknowledged
      """
      alarmlist = self.getSelectedAlarms()
      
      #Only those with a latch severity make the cut
      needsack = []
      for alarm in alarmlist :
         if ("latched" in alarm.get_state(name=True).lower())  :
            needsack.append(alarm)
      return(needsack) 
   
   
   def actionValid(self) :
      """ Action is only valid if there is at least one alarm that
          needs to be acknowledged
          Returns:
            True/False
      """
      valid = False
      needsack = self.getAlarmsToBeAcknowledged()
      
      if (len(needsack) > 0) :
         valid = True
      return(valid)
   
   def configToolBarAction(self) :
      """ Configure the toolbar button as appropriate """
      alarmlist = self.getAlarmsToBeAcknowledged()
      self.setEnabled(True)
 
      if (len(alarmlist) == 0) :
         self.setEnabled(False)
      else :
         self.setEnabled(True)
   
   def performAction(self) :            
      """ Acknowledge the list of alarms """     
      producer = OverrideProducer(getManager().type,'Latched')      
      alarmlist = self.getSelectedAlarms()      
      for alarm in alarmlist :        
         producer.ack_message(alarm.get_name())

     
   
#UnShelve selected alarm/alarms      
class UnShelveAction(Action) :
   def __init__(self,parent,*args,**kwargs) :
                  
      self.icon = QtGui.QIcon("address-book--minus.png")
      self.text = "Shelf Manager"
      self.tip = "Shelf Manager"
      
      self.actionword = "Unshelve"
      
      super(UnShelveAction,self).__init__(parent,*args,**kwargs)

   #Configure the toolbar as appropriate
   def configToolBarAction(self) :
      alarmlist = self.getSelectedAlarms()
      
      if (len(alarmlist) == 0) :
         self.setEnabled(False)
      else :
         self.setEnabled(True)
   
 
   #Unshelve the selected alarms      
   def performAction(self) :
      alarmlist = self.getSelectedAlarms() 
      
      message = None
      if (len(alarmlist) == 0) :
         message = "Select an alarm remove from shelf"
            
         msgBox = QtWidgets.QMessageBox()
         msgBox.setIcon(QtWidgets.QMessageBox.Warning)
         msgBox.setText(message)
         msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
         reply = msgBox.exec()
         return
      
      confirm = confirmAlarms(alarmlist,"Unshelve")
      if (not confirm) :
         return
      
      for alarm in alarmlist :
         alarm.UnShelveRequest()


