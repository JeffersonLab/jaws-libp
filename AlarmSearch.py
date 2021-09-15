from CheckableComboBox import *
from utils import *


#Mix between CheckableComboBox and Autocomplete search box
class AlarmSearch(CheckableComboBox) :
   """ Access to alarms in an auto-complete, checkable combobox
   """   
   def __init__(self,alarmlist,parent=None) :
      """ 
         .. automethod:: __init__
         .. rubric:: Methods
         
         Create an AlarmSearch widget
         Parameters:
            alarmlist (list) : list of alarms to populate combobox
            parent : parent of widget
      """
      
      super(AlarmSearch,self).__init__(parent)
      
      #List of alarms that have been selected
      self.selected = []
      
      #Add "all" to the list.
      self.alarmlist = ["All"]
      self.alarmlist.extend(alarmlist)
      
      self.addItems(self.alarmlist)
      
      #Because of auto-complete. 
      self.lineEdit().setReadOnly(False)
           
      self.lineEdit().returnPressed.connect(self.takeItem)
      self.textActivated.connect(self.selectItem) ###
     
   
   def setSelection(self,preselectedalarms) :
      """ 
         Handle preselected alarms
         Parameters:
            preselectedalarms (list) : list of preselected alarms
      """
     
      if (not preselectedalarms or len(preselectedalarms) == 0) :
         self.selected = []
      else :
         for alarm in preselectedalarms :
           # self.selected.append(alarm.get_name())
            self.selectItem(alarm.get_name())

   def addItem(self, text, data=None):
      """ 
         Add an item to the combobox
         Parameters:
            text (str) : text do display
            data (str) : optional parameter
      """
      super().addItem(text,data)
                
      if (text in self.selected) :
         self.selectItem(text)
        
   def sizeHint(self) :
      """ Override the widget's initial size hint
      """
      size = QtCore.QSize()
      height = 1 
      width = 250
      size.setHeight(height)
      size.setWidth(width)      
      return(size)

   def getSelectedAlarms(self) :
      """ Return the alarms that have been selected from the dropdown
      """
      alarmlist = []
      numrows = self.model().rowCount()
      for row in range(numrows) :
         if (row == 0) :
            continue
         alarm = self.model().item(row)
         if (alarm.checkState()) :
            alarmlist.append(alarm.text())
      return(alarmlist)
      

   def selectItem(self,alarmname) :
      """ 
         When user clicks an alarm checkbox
         Parameters:
            alarmname (str) : selected alarm name            
      """
      if (len(alarmname) == 0) :
         return
      if (alarmname.lower() == "all") :
         return
      
      #Access the checkbox model's alarm per it's name
      itemlist = self.model().findItems(alarmname)
      
      if (len(itemlist) == 0) :
         return      
      item = itemlist[0]   
      
      print("   SELECTEDITEM:",alarmname)
      #If not checked, check it
      if (not item.checkState()) :
         item.setCheckState(Qt.Checked)
      
      #This prevents the combobox from closing when an item is selected.   
      if self.closeOnLineEditClick:
         self.hidePopup()
      else:
         self.showPopup()
   

   def takeItem(self) :      
      """ Called when <Return> is pressed. Selects item in lineEdit()
      """
      alarmname = self.lineEdit().text()  
      if (alarmname.lower() == "all") :
         return
        
      itemlist = self.model().findItems(alarmname)
      if (len(itemlist) == 0) :        
         return    
      
      self.selectItem(alarmname)
      
   def updateText(self):
      """ Update the lineEdit() text when selections are made
      """ 
      
      super().updateText()
      text = self.lineEdit().text()
      if (len(text) == 0) :
         self.lineEdit().setText("Select Alarms")
 
   def updateSearch(self,alarmlist) :
      """ 
         Update the search box with the latest set of alarms.
         Parameters:
            alarmlist (list) : list of alarms to display          
      """

      self.clear()
      self.alarmlist = ["All"]
      self.alarmlist.extend(alarmlist)
     
      count = 0
      for alarmname in self.alarmlist :
         self.addItem(alarmname)
         item = self.model().item(count,0)
     
      completer = QtWidgets.QCompleter(alarmlist)
      completer.setCaseSensitivity(0)
      self.setCompleter(completer)
      
      if (len(self.selected) == 0) :
         
         self.setEditText("Select Alarms")
     
