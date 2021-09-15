import time 
import traceback
import subprocess
import sys

from PyQt5.QtCore import Qt, QObject, pyqtSignal, QRunnable,QThread

from jlab_jaws_helper.JAWSConnection import *
from jlab_jaws_helper.JAWSAlarm import *

#Signals available from running worker.
#Must inherit from QObject, which can emit signals
class WorkerSignals(QObject) :
   finished = pyqtSignal()
   error = pyqtSignal(tuple)
   result = pyqtSignal(object)
   progress = pyqtSignal(object)

         
class JAWSWorker(QRunnable) :
   def __init__(self,fn,topic,*args,**kwargs) :
      super(JAWSWorker,self).__init__()
      
      
      #fn is the function in the GUI to call from the thread
      #In this case it is AlarmProcessor.GetAlarms()
      self.fn = fn
      self.topic = topic
      #self.delay = delay
      
      #Possible arguments
      self.args = args
      self.kwargs = kwargs
      self.running = True
      self.signals = WorkerSignals()
      
      # Add the callback to our kwargs
      self.kwargs['topic'] = topic
      
      
   #Stop the thread   
   def Stop(self) :
      print("STOP")
      #self.signals.finished.emit()
   
   #The thread continues to run as long as the application is 
   #up. When user wants to quit, self.running is set to False 
   def run(self) :      
      '''
      Initialise the runner function with passed args, kwargs.
      '''
      
      # Retrieve args/kwargs here; and fire processing using them
      try:
         result = self.fn(*self.args, **self.kwargs)
      except:
         traceback.print_exc()
         exctype, value = sys.exc_info()[:2]
         self.signals.error.emit((exctype, value, traceback.format_exc()))
      else:
         self.signals.result.emit(result)  # Return the result of the processing
      finally:
         self.signals.finished.emit()  # Done

      


#worker thread (generic)    
class Worker(QRunnable) :
   def __init__(self,fn,delay = 0.5,*args,**kwargs) :
      super(Worker,self).__init__()
      
      #fn is the function in the GUI to call from the thread
      #In this case it is AlarmProcessor.GetAlarms()
      self.fn = fn
      self.delay = delay
      
      #Possible arguments
      self.args = args
      self.kwargs = kwargs
      self.running = True
      
      #Worker will emit a signal upon return from GUI call
      self.signals = WorkerSignals()
   
   def SetDelay(self,delay) :
      self.delay = delay   
   
   #The thread continues to run as long as the application is 
   #up. When user wants to quit, self.running is set to False 
   def run(self) :      
      while (self.running) :
         try :
            #Call the proscribed function
            result = self.fn(*self.args,**self.kwargs)
            
         except :
            traceback.print_exc()
         else :
            #emit the result. The GUI will pick up the result to process
            self.signals.output.emit(result)
         
         self.delay = 0.5
         delay = self.delay  
         #Wait, and do it again
         time.sleep(delay)
   
   #Stop the thread   
   def Stop(self) :
      self.running = False
