from PyQt5.QtCore import Qt

from utils import *
from Actions import *

""" 
   TO DO:
      Update buttons with new state 
      Acknowledge

"""
   
#Parent property dialog
#Active Alarms have slightly different properties than Shelved
class PropertyDialog(QtWidgets.QDialog) :
   def __init__(self,alarm,parent=None,*args,**kwargs) :
      super(PropertyDialog,self).__init__(None,*args,**kwargs)
      
      self.row = None
      self.alarm = alarm
      
      name = True
      #These properties are common to both types of dialog
      self.propwidgets = {
        
         'name' : 
            {'widget' : None, 'command' : self.alarm.get_name,
             'label': "Name:", 'static' : True},
         
         'type' : 
            {'widget' : None, 'property' : 'alarm_class',
            'label' : "Class:", 'static' : True},
         
         'trigger' :
            {'widget' : None, 'command' : self.alarm.get_producer,
            'label' : "Trigger:", 'static' : True},
         
         'location' :
           { 'widget' : None, 
           'property' : 'location',
            'label'   : "Location:", 'static' : True},
         
         'category' :
            {'widget' : None, 
            'property' : 'category',
            'label' : "Category:", 'static' : True},
      }
      
      self.setModal(0)
      self.setSizeGripEnabled(True)
      
      #mainlayout = QtWidgets.QGridLayout()
      
      
      
      layout = QtWidgets.QGridLayout()
      layout.setHorizontalSpacing(10)
      self.layout = layout
      
      #Add these first. The individual dialogs will add their 
      #specialized properties. Then, the parent will add the rest
      #of the common props.
      self.addProperty('name')
      self.addProperty('type')
      self.addSpacer()
      
      groupbox = QtWidgets.QGroupBox(self.alarm.get_name() + " Properties")
      groupbox.setLayout(layout)
      vlayout = QtWidgets.QVBoxLayout()
      
      #Don't let the widget be resized
      vlayout.setSizeConstraint(3)
      vlayout.addWidget(groupbox)
     
      buttons = self.makeButtons()
      vlayout.addWidget(buttons)
                                 
      self.setLayout(vlayout)
      self.setWindowTitle(self.alarm.get_name())
      
      self.show()
   
  
   #Properties can be static. If that's the case, they
   #will not be updated when the alarm changes state   
   def isStatic(self,prop) :
      static = False
      if ("static" in self.propwidgets[prop]) :
         static = True
      return(static)
   
   def getPropertyVal(self,prop) :
      propconfig = self.propwidgets[prop]
      if ('command' in propconfig and propconfig['command'] != None) :
         command = propconfig['command']
         val = command()
      elif ('property' in propconfig and propconfig['property'] != None) :
         val = self.alarm.get_property(propconfig['property'],name=True)
      
            
      format = False
      if ("format" in propconfig) :
         val = FormatTime(val)
      
      return(val)
      
   #Add a simple property widget.
   #Comprised of a label for the property name
   #and a label displaying the value.
   #The value label is returned to be updated if applicable
   def addProperty(self,prop) :
      
      row = self.nextRow()
      layout = self.layout
     
      #The property name   
      text = self.propwidgets[prop]['label']
      label = MakeLabel(text)
      layout.addWidget(label,row,0) 
      
      #Display the property's value
      val = self.getPropertyVal(prop)
      label = QtWidgets.QLabel(val)
      layout.addWidget(label,row,1)
      return(label)
   
   def reset(self) :
      self.configureProperties()
      
   #Update dynamic properties and buttons
   def configureProperties(self) :
      
      for prop in self.propwidgets :
         
         if (not self.isStatic(prop)) :
            self.updateProperty(prop)
      self.updateButtons()
      
   def updateButtons(self) :
      pass
      
   #Update the property if its value changes.
   def updateProperty(self,prop) :
      
      widget = self.propwidgets[prop]['widget']        
      if (widget ==  None) :
         return       
      val = self.getPropertyVal(prop)  
      widget.setText(val)

   #Common properties to add to the PropertyDialog
   def addProperties(self) :
      layout = self.layout
       
      self.addSpacer()
      self.addProperty('trigger')
      self.addLatching()
  
      self.addSpacer()
      
      self.addProperty('location')
      self.addProperty('category')
      self.addSpacer()
      
      #These are special widgets
      #self.addURL()
      self.addScreen()
   
   #Spacer widget to insert blank row   
   def addSpacer(self) :
      row = self.nextRow()
      layout = self.layout
      spacer = QtWidgets.QLabel()
      layout.addWidget(spacer,row,0)
   
   #Little utility so that it's not necessary to keep track
   #of the rows in case more/less are needed.
   def nextRow(self) :
      row = self.row
      if (row != None) :
        row = row + 1
      else :
         row = 0
      self.row = row
      return(row)
   
   
   #The following are specialized widgets
   def addLatching(self) :
      row = self.nextRow()
      layout = self.layout
      label = MakeLabel("Latching:")
      layout.addWidget(label,row,0)
      
      latching = self.alarm.get_latching()
      text = "True"
      if (not latching) :
         text = "False"
      
      latchlabel = QtWidgets.QLabel(text)
      layout.addWidget(latchlabel,row,1)
      
   #EDM screen assigned to alarm
   def addScreen(self) :
      row=self.nextRow()
      layout = self.layout
      label = MakeLabel("Screen:")
      layout.addWidget(label,row,0)
      
      screenpath = self.alarm.get_property('screen_path')
      screenpath = "Push for your screen"
      screenbutton = QtWidgets.QPushButton(screenpath)
      layout.addWidget(screenbutton,row,1)
   
   #Reference url  
   def addURL(self) :
      row = self.nextRow()
      layout = self.layout
      
      label = MakeLabel("Documentation:")
      layout.addWidget(label,row,0)
      
      docurl = self.alarm.GetURL()
      urllabel = QtWidgets.QLabel()
      
      urllabel.setText(
         "<a href=\"http://jlab.org/\">Alarm wiki for " + 
            self.alarm.get_name() + "</a>")
      urllabel.setTextFormat(Qt.RichText)
      urllabel.setTextInteractionFlags(Qt.TextBrowserInteraction)
      urllabel.setOpenExternalLinks(True)
      layout.addWidget(urllabel,row,1)
   
   #close the dialog
   def closeDialog(self) :
      self.close()
   

      
#Create a ShelfPropertyDialog for use with the shelf manager 
class ShelfPropertyDialog(PropertyDialog) :
   def __init__(self,parent=None,*args,**kwargs) :   

      super(ShelfPropertyDialog,self).__init__(parent,*args,**kwargs)
     
      #Add specialize shelf properties to the propwidget dictionary
      self.propwidgets['shelftime'] = \
                     {'widget' : None, 'command' : self.alarm.GetShelfTime,
                     'format' : True, 'label' : "Date Shelved:"}
      self.propwidgets['exptime'] = \
                      {'widget' : None, 
                      'command' : self.alarm.GetShelfExpiration,
                      'format' : True, 'label' : "Expires:"}      
      self.addProperties()
    
   #Static/common properties will be created by the parent dialog
   def addProperties(self) :
      
      for prop in self.propwidgets :
         if (not self.isStatic(prop)) :
           
            widget = self.addProperty(prop)
            self.propwidgets[prop]['widget'] = widget
         
      super().addProperties()
      self.configureProperties()
   
   #Create the buttons appropriate for the ShelfProperty
   def makeButtons(self) :
      layout = QtWidgets.QHBoxLayout()
      
      self.unshelveaction = UnShelveAction(self)
      button = QtWidgets.QPushButton("Un-Shelve")
      button.clicked.connect(self.UnShelveAlarm)
      layout.addWidget(button)
      self.unshelvebutton = button
 
      button = QtWidgets.QPushButton("close")
      layout.addWidget(button)
      button.clicked.connect(self.close)
      
      self.shelfaction = ShelfAction(self)
      button = QtWidgets.QPushButton("Override")
      button.clicked.connect(self.ShelveAlarm)      
      layout.addWidget(button)
      self.shelfbutton = button
     
      widget = QtWidgets.QWidget()
      widget.setLayout(layout)
      return(widget)     
   
   #Unshelve the alarm
   def UnShelveAlarm(self) :
             
      self.unshelveaction.performAction()
      self.unshelvebutton.setEnabled(False)
   
   #Update the "un-shelve" button if shelf state changes 
   def updateButtons(self) :
      self.unshelvebutton.setEnabled(True)
      if (not self.alarm.IsShelved()) :
         self.unshelvebutton.setEnabled(False)


#ActiveAlarm specific property dialog            
class AlarmPropertyDialog(PropertyDialog) :
   def __init__(self,parent=None,*args,**kwargs) :
      
      self.ackbutton = None
      self.shelfbutton = None
      super(AlarmPropertyDialog,self).__init__(parent,*args,**kwargs)
      
      #Add specialize shelf properties to the propwidget dictionary
      self.propwidgets['lastalarm'] = \
                      {'widget' : None, 'command' : self.alarm.get_state_change,
                      'format' : True, 'label' : "State Change:"}
     # self.propwidgets['acktime'] = \
      #                {'widget' : None, 
       #               'command' : self.alarm.GetAckTime,
        #              'format' : True, 'label' : "Last Ack:"}
            
      self.addProperties()

   #Active alarms have fields for "last alarm" and "last ack'd" times.
   def addProperties(self) :
      self.propwidgets['lastalarm']['widget'] = self.addProperty('lastalarm')     
      #if (self.alarm.IsLatching()) :
       #  self.propwidgets['acktime']['widget'] = self.addProperty('acktime')
      
      #Add the common properties defined in PropertyDialog
      super().addProperties()
      #They will be re-configured if changed
      self.configureProperties()
   
   #Update dynamic properties
   def configureProperties(self) :
      super().configureProperties()
      
      #Updating the border is specialized
      self.updateBorder()
      self.updateButtons()
   
   #Configure buttons based on current state
   def updateButtons(self) :
      #return
      #self.shelfbutton.setEnabled(True)
      
      state = self.alarm.get_state(name=True)
      if (self.ackbutton == None) :
         return
      if (state != None and "latched" in state.lower()) :
         self.ackbutton.setEnabled(True)
      else :
         self.ackbutton.setEnabled(False)
                  
   #Update the border based on the alarm's severity
   def updateBorder(self) :
      color = GetStatusColor(self.alarm.get_sevr())
      if (color == None) :
         return
      border = "border: 5px solid " + color
      stylesheet = self.styleSheet()
      style = "QDialog" + "{" + "border: 5px solid " + color + ";" +  "}"      
      self.setStyleSheet(style)

      
   #Create the buttons appropriate for the AlarmProperty
   def makeButtons(self) :
      layout = QtWidgets.QHBoxLayout()
      
      if (self.alarm.get_latching()) :
         button = QtWidgets.QPushButton("Acknowledge")
         layout.addWidget(button)
         self.ackbutton = button
         button.clicked.connect(self.acknowledgeAlarm)
      
      
      button = QtWidgets.QPushButton("Close")
      layout.addWidget(button)
      button.clicked.connect(self.closeDialog)
      
     # self.shelfaction = ShelfAction(self)
      #self.shelfbutton = QtWidgets.QPushButton("Override")
      #self.shelfbutton.clicked.connect(self.ShelveAlarm)
      
      #layout.addWidget(self.shelfbutton)
           
      widget = QtWidgets.QWidget()
      widget.setLayout(layout)
      
      return(widget)  
   
   def acknowledgeAlarm(self) :
      action = AckAction(self)
      action.performAction(self.alarm.get_name())
      