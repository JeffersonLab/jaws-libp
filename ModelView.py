#NOTE ABOUT METHOD AND VARIABLE NAMES
# --- self.myvariable     -- variable for this application
# --- def MyMethod()      -- method implemented for this application
# --- def libraryMethod() -- method accessed/overloaded from a python library

#Contains the ModelView class inherited by AlarmModel and OverrideModel

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QBrush
from PyQt5.QtCore import Qt, QObject,QThreadPool,QThread
from utils import *

#Parent ModelView. AlarmModel and OverrideModel inherit         
class ModelView(QtCore.QAbstractTableModel) :
   
   def __init__(self,data=None,parent = None, *args) :
      super(ModelView,self).__init__(parent,*args) 
      self.data = data or []
      
      self.columnconfig = getManager().columns
      self.columnlist = list(self.columnconfig)
      self.filtercols = {}
      
   #rowCount must be overloaded. 
   #Overload it here, since the same for all children 
   def rowCount(self,index) :
      return(len(self.data))
   
   #columnCount must be overloaded
   def columnCount(self,index) :      
      
      return(len(self.columnlist))
   
   def GetColumnName(self,col) :
       return(self.columnlist[col])
   
   def setHeader(self,columname,filtered) :      
      headercol = getModel().GetColumnIndex(columname)
      if (filtered) :         
         self.setFilter(headercol,True)  
         getManager().getRemoveFilterAction().setChecked(True)
      else :                  
         getManager().getRemoveFilterAction().setState()
         self.setFilter(headercol,False)

        
   def GetColumnIndex(self,property) :
      
      if (not property in self.columnlist) :
         index = None
      else :
         index = self.columnlist.index(property)
      
      return(index)
   
   def GetColWidth(self,property) :
      width = None
      
      if (property in self.columnconfig) :
         if ('size' in self.columnconfig[property]) :
            width = self.columnconfig[property]['size']
         
      return(width)   
   
          
   def applyChanges(self,showlist=None) :
      
      if (showlist == None) :
         showlist = []
         
      #The horizontal header for our table model
      horizheader = getTable().horizontalHeader()
      
      #The col, is the "logical" index for the model.
      #it's the one that stays constant, no matter what the 
      #user sees.
      for col in range(self.columnCount(0)) :        
         #The "visualindex" is the column index that the user 
         #is actually seeing. We want to move the visual index
         #if the user changes the order in the "show" box.
         visualindex = horizheader.visualIndex(col)
         
         #Get the header text for this column
         header = self.headerData(col,Qt.Horizontal,Qt.DisplayRole)
         
         #If the header (lower case) is in the list of properties
         #to show...
         if (header.lower() in showlist) :
            #Where in the showlist is it? 
            index = showlist.index(header.lower())
            
            #Make sure the "logical" column is showing.
            getTable().horizontalHeader().showSection(col)
            #Now, move the visual column to the new index.
            getTable().horizontalHeader().moveSection(visualindex,index)          
         else :
            #If in the "hide" list, simply hide the column
            getTable().horizontalHeader().hideSection(col)
      
      #Some columns are wider than others, make sure the header has the
      #correct width for the property
      self.configureColumns()
      
      #Force the manager to resize to the new size of the table.
      getManager().setSize()
   
   #Return the list of columns in the order that they are visible.
   def VisibleColumnOrder(self) :

      options = []
      hidden = []
      horizheader = getTable().horizontalHeader()
      
      #Traverse each column in the table/model
      for col in range(self.columnCount(0)) :        
         
         #The "visualindex" is the column index that the user 
         #is actually seeing. We want the combobox to be in the same
         #order as the columns
         #if the user changes the order in the "show display" box.
         visualindex = horizheader.visualIndex(col)
         
         #Get the header text for this column
         header = self.headerData(col,Qt.Horizontal,Qt.DisplayRole)
         if (getTable().isColumnHidden(col)) :
            hidden.append(header.lower())
         else :
            #Insert the header at the visible index.        
            options.insert(visualindex,header.lower())
      
      for header in hidden :
         
         options.append(header)
      
      
      
      return(options)
  
   def configureColumns(self) :
      modelindex = self.GetColumnIndex
      for prop in self.columnlist :
         width = self.GetColWidth(prop)
         if (width != None) :
            getTable().setColumnWidth(modelindex(prop),width)
   
   def UpdateModel(self) :
      getManager().setSize()   

   #Add alarm to the data. 
   def addAlarm(self,alarm) :
      #print(QThread.currentThread())
      #Remove the alarm from the data first.
      self.layoutAboutToBeChanged.emit()    
      if (alarm in self.data) :
         self.data.remove(alarm)
      
      #Need to emit this signal so that the TableView will be ready
      
      #add the alarm to to the model data.
      self.data.append(alarm)
      #Emit signal to the TableView to redraw
      self.layoutChanged.emit()
      
      getManager().getToolBar().configureToolBar()
      getManager().configureProperties(alarm)
      getManager().setSize()
      
      if (getManager().overridedialog != None) :
         getManager().overridedialog.reset()
      
         
   #Remove the alarm. 
   def removeAlarm(self,alarm) :
      
      #Double check that the alarm is in the dataset.
      if (alarm in self.data) :        
         #Warn the TableView
         self.layoutAboutToBeChanged.emit()
         #Actually remove the alarm
         self.data.remove(alarm)   
         #Emit signal to TableView to redraw
         self.layoutChanged.emit()
         
      getManager().getToolBar().configureToolBar()
      getManager().configureProperties(alarm)
      getManager().setSize()
      
      if (getManager().overridedialog != None) :
         getManager().overridedialog.reset()

     
   #Configure the header if the data is filtered      
   def setFilter(self,column,filtered=False) :
      
      #If the user filters the data from a filter menu.
      #indicate that on the column header by adding a little
      #filter icon to the columns that have been filtered.
      #try :
      if (not filtered) :
         self.filtercols[column] = False
      else :
         self.filtercols[column] = True
      self.headerDataChanged.emit(Qt.Horizontal,column,column)
 
   
   #Display headers for the columns
   def headerData(self,section,orientation,role) :
      #sourcemodel = self.sourceModel()
      
      if (role != Qt.DisplayRole and role != Qt.DecorationRole) :
         return
      if (orientation != Qt.Horizontal) :
         return      
      try :
         #Try to add the filter image to the header to show it's filtered 
         if (role == Qt.DecorationRole and self.filtercols[section]) :
            return (QtGui.QPixmap("funnel--plus.png"))
         elif (role == Qt.DecorationRole) :
            
            return("") 
      except : 
         return("")
      
      if (role == Qt.DisplayRole) :
         return(self.columnlist[section].title())
      
      return(QtCore.QAbstractTableModel.headerData(self,section,orientation,role))


       
#AlarmModel contains the data to disaply in the TableView widget    
class AlarmModel(ModelView) :
   def __init__(self,data=None,parent = None, *args) :
      super(AlarmModel,self).__init__(data,parent,*args) 
      
   #Overloaded function that must be defined.      
   def data(self,index,role) :
      #The index (contains both x,y) and role are passed.  
      #The roles give instructions about how to display the model.
      row = index.row()
      col = index.column()
       
      #Center column 2, the timestamp
      if (role == Qt.TextAlignmentRole) : 
         return(Qt.AlignCenter)
      
      alarm = self.data[row] 
      (sevr,latch) = self.get_sevrDisplay(alarm) 
      
      if (col == self.GetColumnIndex('status')) :
         if (role == Qt.BackgroundRole) :
            if (latch != None) :
               return(GetQtColor(latch))
      
         if (role == Qt.DecorationRole) :
            image = GetStatusImage(sevr)
            if (image != None) :
               return(QIcon(image))
      
      #Insert the appropriate information into the display, based
      #on the column. Column "0" is handled by the StatusDelegate
      if role == Qt.DisplayRole :
         if (col == self.GetColumnIndex('status')) :
            #Does the alarm have a severity?
            
            if (sevr == None) :
               sevr = "ALARM"
            
            return(sevr)
         
         if (col == self.GetColumnIndex('name')) :
            return(alarm.get_name())
         
         if (col == self.GetColumnIndex('timestamp')) :
            timestamp = alarm.get_state_change()
            if (timestamp != None) :
               return(timestamp.strftime("%Y-%m-%d %H:%M:%S"))
                        
         if (col == self.GetColumnIndex('category')) :
            return(alarm.get_property('category',name=True))
         if (col == self.GetColumnIndex('location')) :
            return(alarm.get_property('location',name=True))  
         if (col == self.GetColumnIndex('priority')) :
            return(alarm.get_property('priority',name=True))
   
   def get_sevrDisplay(self,alarm) :
      
      state = alarm.get_state(name=True)
      latching = alarm.get_latching()
      
      sevr = alarm.get_sevr(name=True)
      latch = None    
      if (latching) :
         if (state.lower() == "latched") :
            latch = sevr
         elif(state.lower() == "normallatched") :
            latch = sevr
            sevr = "NO_ALARM"
         elif (state.lower() == "active") :
            latch = None
         
      return(sevr,latch)
  
     
   

#proxyModel->invalidate();
class ProxyModel(QtCore.QSortFilterProxyModel) :
   def __init__(self,*args,**kwargs) :
      super(ProxyModel,self).__init__(*args,**kwargs)
      
      self.sortpriority = []
   
   #Sorting by status is a custom sort, so need to override proxymodel's
   #lessThan method
   def lessThan(self,leftindex,rightindex) :
      #The sort column 
      col = leftindex.column()
      
      #Get the header text for this column
      header = self.sourceModel().headerData(col,Qt.Horizontal,Qt.DisplayRole)
      
      #If not the status column, just sort as normal
      if (not header.lower() == "status") :
         return(super(ProxyModel,self).lessThan(leftindex,rightindex))
      
      #These values will be put somewhere better...
      statusvals = ['LATCHED','MAJOR','ALARM','MINOR',None]
      
      #Get the status of the "left" and "right" alarm
      leftalarm = self.sourceModel().data[leftindex.row()]
      leftsevr = leftalarm.get_sevr()
      
      rightalarm = self.sourceModel().data[rightindex.row()]
      rightsevr = rightalarm.get_sevr()
      
      #The statusvals list is in order of importance. 
      #So, compare the index for the alarm's status. Lower wins
      leftrank = statusvals.index(leftsevr)
      rightrank = statusvals.index(rightsevr)
      
      if (leftrank < rightrank) :
         return(True)
      else :
         return(False)
    
   def filterAcceptsRow(self,row,parent) :
      
      filters = getManager().filters
      if (len(filters) == 0) :
         
         getManager().makeFilters()
      
      index = self.sourceModel().index(row,0,parent)      
      alarm = self.sourceModel().data[row]
      
      keep = True
      for filter in getManager().filters :
         
         keep = filter.ApplyFilter(alarm)
               
         if (not keep) :
            return(False)
      if (keep) :
         return (super(ProxyModel,self).filterAcceptsRow(row,parent))
      
      

      
