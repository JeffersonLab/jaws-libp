""" 
.. module:: AlarmProcessor
   :synopsis : Inherits JAWSProcessor 
.. moduleauthor::Michele Joyce <erb@jlab.org>
"""

from jlab_jaws_helper.JAWSProcessor import JAWSProcessor

class AlarmProcessor(JAWSProcessor) :
   def __init__(self) :
      
      #Don't need to register for overridden-alarms because we'll
      #use the 'alarm-state' to display
      topics = ['registered-alarms','active-alarms','alarm-state']
      #topics = ['active-alarms','alarm-state']
      super(AlarmProcessor,self).__init__(topics)
   

         
   def getRegisteredAlarms(self) :
      return(self.alarm_list.keys())