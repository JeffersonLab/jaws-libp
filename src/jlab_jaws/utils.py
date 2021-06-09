""" 
.. currentmodule:: jlab_jaws.utils
.. automodule: utils
   :synopsis : common utilities for use with the JAWS alarm system
   

"""

import time
from datetime import datetime
import pytz

def convert_timestamp(seconds) :
   """ 
      .. automethod:: convert_timestamp
      .. rubric:: Methods
            
      Convert the message timestamp to local timezone.
       
       
       Parameters:
         seconds(int) : number of seconds
       
       Returns:
         datestring in local time: "2021-06-09 09:26:09-04:00"
      
   """     

   #Work in utc time, then convert to local time zone.    
   ts = datetime.fromtimestamp(seconds//1000)
   utc_ts = pytz.utc.localize(ts)
   #Finally convert to EST.
   est_ts = utc_ts.astimezone(pytz.timezone("America/New_York"))
   return(est_ts)
