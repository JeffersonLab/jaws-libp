from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

from utils import *

class DurationWidget(QtWidgets.QGroupBox) :
   """ QGroupBox containing options for override duration
   """
   def __init__(self,parent=None,*args,**kwargs) :           
      """ 
         .. automethod:: __init__
         .. rubric:: Methods
         
         OverrideWidget's duration options
         Parameters:           
            parent : override dialog
      """          
      super(DurationWidget,self).__init__("Override Duration",parent,*args,**kwargs)
           
      self.durationoptions = []
      layout = QtWidgets.QGridLayout()
      
      #Radiobutton for each duration option
      oneshot = DurationOption("OneShot override",self)      
      quick = DurationOption("Quick select",self)
      custom = DurationOption("Custom duration",self)
      disable = DurationOption("Remove from service",self)
      
      self.quickoption = quick
      self.customoption = custom
      
      self.durationoptions.append(oneshot)
      self.durationoptions.append(quick)
      self.durationoptions.append(custom)
      self.durationoptions.append(disable)
      layout.addWidget(oneshot,0,0)
      layout.addWidget(quick,1,0)
      layout.addWidget(custom,2,0)
      layout.addWidget(disable,3,0)
      
      #Add the QuickSelect combo box.
      self.quickselect = QuickSelectCombo(self)  
      layout.addWidget(self.quickselect,1,1)
      
      #And the CustomDuration spinners 
      self.custom  = CustomDuration(self)
      layout.addWidget(self.custom,2,1)
      
      self.setLayout(layout) 
    
   def durationType(self) :
      """ Which duration option was selected?
      """      
      durationtype = None
      for option in self.durationoptions :
         if (option.isChecked()) :
            durationtype = option.getType()     
      return(durationtype)
     
   def calcDuration(self) :
      """ Calculate the duration for timed overrides
      """
      if (self.durationType() == "quick") :
         return(self.quickselect.calculateDuration())
      if (self.durationType() == "custom") :
         return(self.custom.calculateDuration()) 


   def selectDurationOption(self,val=None) :
      """ Called when a duration option is "activated"
          NOTE: val will always be True               
      """      
      
      #Clear the quickselect combo widget and the custom time spinners
      if (self.durationType() != "quick") :
         self.quickselect.clearSelection()
      if (self.durationType() != "custom") :
         self.custom.clearSpinners()
         
  
   def clearDuration(self) : 
      """ Clears all duration options when dialog reopened
      """
      for option in self.durationoptions :        
         option.setAutoExclusive(False) 
         option.setState(False)
         option.setAutoExclusive(True)
      self.selectDurationOption()

         
class DurationOption(QtWidgets.QRadioButton) :
   """ Radiobutton for use to select override duration type
   """  
   def __init__(self,label,parent=None,*args,**kwargs) :
                 
      """
         .. automethod:: __init__
         .. rubric:: Methods
         
         Individual duration option
         Parameters:       
            label  : label for option    
            parent : DurationWidget
      """          

      super(DurationOption,self).__init__(label,parent,*args,**kwargs)
      
      self.parent = parent     
      self.durationoption = label.split()[0].lower()
      self.clicked.connect(self.selectDurationOption)
      
   def selectDurationOption(self,checked) :
      print(self.durationoption,checked)
      
   def getType(self) :
      """ Duration option type (oneshot,quickselect,custom,disabled)
      """
      return(self.durationoption)
   
   def setState(self,checked=True) :
      """ Set the state of the radiobutton
      """
      self.setChecked(checked)
      
class QuickSelectCombo(QtWidgets.QComboBox) :
   """ Combobox with list of canned durations
   """  
   def __init__(self,parent=None, *args,**kwargs) :
      """
         .. automethod:: __init__
         .. rubric:: Methods
         
         Parameters:       
            parent : DurationWidget
      """          
      super(QuickSelectCombo,self).__init__(parent,*args,**kwargs)
      
      self.parent = parent
      selectlist = ["Select Duration"]
      for duration in QUICKDURATIONS :
         selectlist.append(QUICKDURATIONS[duration]['text'])
      
      for reason in selectlist :
         self.addItem(reason)  
         
      self.setEditable(False)
      self.setFixedWidth(200)
      
      #User has selected from the combobox
      self.activated.connect(self.selectDurationOption)
   
   def calculateDuration(self) :
      """ Calculate the duration in seconds
      """
      seconds = 0
      text = self.currentText()
      for choice in QUICKDURATIONS :
         label = QUICKDURATIONS[choice]["text"]
         if (label == text) :
            seconds = QUICKDURATIONS[choice]["seconds"]
      return(seconds)
      
   def selectDurationOption(self,index) :      
      """
         If the user selects from the combobox, automatically set the associated
         radiobutton (durationoption)
      """
      if (index > 0) :
         self.parent.quickoption.setState(True)
      else :
         self.parent.quickoption.setState(False)
      self.parent.selectDurationOption(index)
      
   def clearSelection(self) :
      """ Clear previous selection 
      """
      self.setCurrentIndex(0)
   
class CustomDuration(QtWidgets.QFrame) :
   """ hour and minute spinner to define a custom duration
   """
   def __init__(self,parent=None,*args,**kwargs) :
      """
         .. automethod:: __init__
         .. rubric:: Methods
         
         Parameters:       
            parent : DurationWidget
      """               
      super(CustomDuration,self).__init__(parent,*args,**kwargs)
           
      self.parent = parent
           
      layout = QtWidgets.QHBoxLayout()
      layout.setAlignment(Qt.AlignLeft)
      layout.setSpacing(10)
      layout.setContentsMargins(0,0,0,0)
      
      #Create a spinner for the hours and minutes
      hourwidget = DurationSpinner("hours",24,self)
      self.spinhour = hourwidget.spinbox      
      layout.addWidget(hourwidget)
      
      minwidget = DurationSpinner("mins",60,self)
      self.spinmin =  minwidget.spinbox
      layout.addWidget(minwidget)
      
      self.setLayout(layout)
   
   def calculateDuration(self) :
      """ Calculate the duration (in seconds) selected by the spinners
      """
      hours = self.spinhour.value()
      mins = self.spinmin.value()
      
      #turn the hours into minutes
      finalmin = mins + hours * 60
      seconds = finalmin * 60
      return(seconds)

   def selectDurationOption(self) :
      """
         If a spinner is being used, automatically select (deselect) the 
         associated duration option (custom)
      """
      hours = self.spinhour.value()
      mins  = self.spinmin.value()
      
      if (hours > 0 or mins > 0) :
         self.parent.customoption.setState(True)
      else :
         self.parent.customoption.setState(False)
   
   def clearSpinners(self) :
      """ Clear previous selection 
      """ 
      self.spinhour.setValue(0)
      self.spinmin.setValue(0)


class DurationSpinner(QtWidgets.QWidget) :
   """ A spinner used to define a custom override duration
   """
   def __init__(self,which,maxval,parent=None,*args,**kwargs) :
      """ 
         Widget includes a label and spinner
      
         .. automethod:: __init__
         .. rubric:: Methods
         
         Parameters:       
            parent : DurationWidget
      """                 
      super(DurationSpinner,self).__init__(parent,*args,**kwargs)
      
      self.parent = parent
      
      layout = QtWidgets.QHBoxLayout()
      layout.setAlignment(Qt.AlignRight)
      layout.setSpacing(0)
      layout.setContentsMargins(0,0,0,0)
      
      
      label = QtWidgets.QLabel(which)
      label.setFixedWidth(40)
      layout.addWidget(label)
 
      spinbox = QtWidgets.QSpinBox(self)
      spinbox.valueChanged.connect(self.selectDurationOption)
      spinbox.setFixedWidth(50)
      spinbox.setWrapping(True)
      spinbox.setMaximum(maxval)
      layout.addWidget(spinbox)
      self.setLayout(layout)
      self.spinbox = spinbox
            
   def selectDurationOption(self,val) :
      """ Called when spinner is activated.
      """
      self.parent.selectDurationOption()

      
