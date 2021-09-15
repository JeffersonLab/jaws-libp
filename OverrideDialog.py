from PyQt5 import QtCore, QtGui, QtWidgets


from utils import *
from Actions import *
from AlarmSearch import *
from DurationWidget import *

from jlab_jaws_helper.JAWSConnection import *



class OverrideDialog(QtWidgets.QDialog) :
   """ Access to the various Override Options
   """
   def __init__(self,preselectedalarms=None,parent=None,*args,**kwargs) :
      print("OVERRIDE DIALOG")
      
      """ 
         .. automethod:: __init__
         .. rubric:: Methods
         
         Create an OverrideDialog
         Parameters:
            preselectedalarms (list) : list of alarms to pre-selectedalarms
            parent : parent of dialog
      """     
      super(OverrideDialog,self).__init__(parent,*args,**kwargs)
      
      #The override types that can be selected
      self.OVERRIDETYPES = {
          'oneshot' : {'label' : "Oneshot override", 'action' : self.oneShotOverride},
          'quick'   : {'label' : "Quick select", 'action' : self.timedOverride},
          'custom'  : {'label' : "Custom duration", 'action' : self.timedOverride},
          'remove'  : {'label' : "Remove from service", 'action' : self.disableOverride}
      }
        
      self.reason = None    #Reason for override (required)
      self.comments = None  #Optional comments
      
      self.selected = preselectedalarms  #Alarms to override
      if (not preselectedalarms or preselectedalarms == None) :
         self.selected = None
      
      self.setModal(0)
      self.setSizeGripEnabled(True)
      
      #Search widget to selected alarms
      self.searchwidget = SearchWidget(self.getAlarms(),self)
      self.search = self.searchwidget.search
      
      #Duration options
      self.durationwidget = DurationWidget(self) ## Widget imported.
      
      #Reason and comments
      self.reasonwidget = ReasonWidget(self)
      
      #Bottom buttons
      buttonwidget = ButtonWidget(self)
      
      #Add the widgets to the main layout
      mainlayout = QtWidgets.QVBoxLayout()
      
      mainlayout.addWidget(self.searchwidget)
      mainlayout.addWidget(self.durationwidget)
      mainlayout.addWidget(self.reasonwidget)
      mainlayout.addWidget(buttonwidget)
      self.setLayout(mainlayout)
      
      self.setWindowTitle("Override Alarms")
      self.show()
       
   
   
   def checkOverrideConfig(self) :
      """ Check that all required properties have been set.
      """      
      
      reason = self.reasonwidget.getReason()
      durationtype = self.durationwidget.durationType()
      
      message = None
      
      #Have any alarms been selected?
      alarmlist = self.getSelectedAlarms()
      if (len(alarmlist) == 0) :
         message = "Select an alarm to override"      
      elif ("reason" in reason.lower()):
         message = "Need a reason"      
      elif (durationtype == None) :
         message = "Please select an override duration"
            
      #Inform the user if something is missing
      if (message != None) :
         msgBox = QtWidgets.QMessageBox()
         msgBox.setIcon(QtWidgets.QMessageBox.Warning)
         msgBox.setText(message)
         msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
         reply = msgBox.exec()
         return
      
      #Everything's there, override the alarms.
      self.overrideAlarms(alarmlist)

   #Shelve the selected alarms
   def overrideAlarms(self,alarmlist) :
      """ 
         Override the selected alarms
         Parameters:
            alarmlist (list) : list of alarms override
      """
       
      self.reason = self.getReason() #required
      self.comments = self.getComments() #optional
      
      #Call the subroutine for the duration type selected.
      overridetype = self.durationwidget.durationType()
      subroutine = self.OVERRIDETYPES[overridetype]['action'](alarmlist)
                  
   def oneShotOverride(self,alarmlist) :
      """ 
         Oneshot override (clears alarm for this instance only)
         Parameters:
            alarmlist (list) : list of alarms override
      """
      action = OneShotAction(None)    
      action.performAction(self.reason,self.comments,alarmlist)
   
   def timedOverride(self,alarmlist) :
      """ 
         Timed override
         Parameters:
            alarmlist (list) : list of alarms override
      """
      #Calculate the duration of the override (in seconds)
      seconds = self.durationwidget.calcDuration()
      action = TimedOverrideAction(None,seconds)
      action.performAction(self.reason,self.comments,alarmlist)

   def disableOverride(self,alarmlist) :
      """ 
         Disabled (out of service)
         Parameters:
            alarmlist (list) : list of alarms override
      """      
      action = DisableAction(None)
      action.performAction(self.comments,alarmlist)
   
   def getAlarms(self) :
      """ Get a list of the alarm names in the model
      """
      alarms = sorted(getAlarmNames())     
      return(alarms)

   def setSelection(self,preselectedalarms) :
      """ Preselect alarms in the search box
          NOTE: Used when the dialog is called from contextmenu
         
         Parameters:
            preselectedalarms (list) : list of alarms to pre-selectedalarms          
      """     
      
      self.search.setSelection(preselectedalarms)
              
   
   def getSelectedAlarms(self) :
      """ Access the alarms selected for override
      """  
      alarmnames = self.search.getSelectedAlarms()      
      alarmlist = []
      for name in alarmnames :
         alarm = getManager().processor.find_alarm(name)
         alarmlist.append(alarm)
      
      return(alarmlist)
   
   def getReason(self) :
      """ Access the reason selected for override
      """  
      return(self.reasonwidget.getReason())
      
   def getComments(self) :
      """ Access optional comments
      """  
      comments = self.reasonwidget.getComments()
      if (len(comments) == 0) :
         comments = None
      return(comments)
      
        
   def closeDialog(self) :
      """ Close the dialog
      """  
      self.close() #This "close" is the widget's built in subroutine
 
   
   def reset(self) :      
      """ Reset all parameters if the dialog is closed and reopened
      """  
      self.search.updateSearch(self.getAlarms())
      self.reasonwidget.clearReason()
      self.durationwidget.clearDuration()


class SearchWidget(QtWidgets.QGroupBox) :
   """ Auto-complete/checkable combo box displaying alarms 
   """
   def __init__(self,alarmlist,parent=None,*args,**kwargs) :
      """ 
         .. automethod:: __init__
         .. rubric:: Methods
         
         OverrideWidget's search widget
         Parameters:           
            parent : override dialog
      """               
      super(SearchWidget,self).__init__("Active Alarms",parent,*args,**kwargs)
      
      searchlayout = QtWidgets.QGridLayout()
      
      self.search = AlarmSearch(alarmlist,parent)
      searchlayout.addWidget(self.search,0,0)          
      
      self.setLayout(searchlayout)


class ReasonWidget(QtWidgets.QGroupBox) :
   """ Combobox with list of official "reasons" and an optional box for comments
   """

   def __init__(self,parent=None,*args,**kwargs) :
      """ 
         .. automethod:: __init__
         .. rubric:: Methods
         
         Parameters:           
            parent : override dialog
      """               
      super(ReasonWidget,self).__init__("Reason for Override",parent,*args,**kwargs)
      
      reasonlayout = QtWidgets.QGridLayout()      
      self.reasoncombo = ReasonCombo(parent)
      reasonlayout.addWidget(self.reasoncombo,0,1,Qt.AlignHCenter)
      
      label = QtWidgets.QLabel("Comments (opt)")
      reasonlayout.addWidget(label,1,0)
      
      self.reasoncomments = CommentsEdit(parent)
      reasonlayout.addWidget(self.reasoncomments,1,1)
      self.setLayout(reasonlayout)
      
   def clearReason(self) :
      self.setReason(0)
      self.reasoncomments.clearComments()
      
   def getReason(self) :
      """ Get the selected reason
      """
      return(self.reasoncombo.getReason())
     
   def getComments(self) :
      """ Get the optional comments
      """
      return(self.reasoncomments.getComments())  
   
   def setReason(self,index=0) :
      """ Set the reason to the requested index 
      """
      self.reasoncombo.setReason(index)

        
class ReasonCombo(QtWidgets.QComboBox) :
   """ Combobox with list of canned reasons for an override
   """
   
   def __init__(self,parent=None, *args,**kwargs) :
      """ 
         .. automethod:: __init__
         .. rubric:: Methods
         
         Parameters:           
            parent : override dialog
      """               
      super(ReasonCombo,self).__init__(parent,*args,**kwargs)
      
      # List of reasons comes from JAWSConnection
      reasonlist = ["Select Reason"]
      reasonlist.extend(get_override_reasons())
      
      for reason in reasonlist :
         self.addItem(reason)  
      
      self.setEditable(False)    
      #Make sure the width is reasonable.
      self.setFixedWidth(200)
   
 
      
   def setReason(self,index) :
      """ Set the reason to the requested index
      """
      self.setCurrentIndex(index)
      
   def getReason(self) :
      """ Retrieve the selected reason
      """
      return(self.currentText())  

class CommentsEdit(QtWidgets.QPlainTextEdit) :
   """ Optional override comments
   """
   def __init__(self,parent=None,*args,**kwargs) :
      """ 
         .. automethod:: __init__
         .. rubric:: Methods
         
         Parameters:           
            parent : override dialog
      """               
      super(CommentsEdit,self).__init__(parent)
      
      self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
         QtWidgets.QSizePolicy.MinimumExpanding)
      
   def getComments(self) :
      """ Get comments text
      """
      return(self.toPlainText())
   
   def clearComments(self) :
      """ Clear comment box
      """
      self.clear()     
      
   #Override the widget's initial size hint
   def sizeHint(self) :
      size = QtCore.QSize()
      height = 1 
      width = 250
      size.setHeight(height)
      size.setWidth(width)      
      return(size)

class ButtonWidget(QtWidgets.QWidget) :
   """ Buttons for the dialog
   """
   def __init__(self,parent=None,*args,**kwargs) :
      """ 
         .. automethod:: __init__
         .. rubric:: Methods
         
         Parameters:           
            parent : override dialog
      """               
      super(ButtonWidget,self).__init__(parent,*args,**kwargs) 
         
      buttonlayout = QtWidgets.QHBoxLayout()
      
      button = QtWidgets.QPushButton("Cancel")
      buttonlayout.addWidget(button)
      button.clicked.connect(parent.closeDialog)
      
      button = QtWidgets.QPushButton("OK")
      button.clicked.connect(parent.checkOverrideConfig)
      buttonlayout.addWidget(button)
    
      self.setLayout(buttonlayout)
