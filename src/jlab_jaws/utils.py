""" 
.. module:: utils
   :synopsis : common utilities
"""

import time
from datetime import datetime
import pytz

def convert_timestamp(seconds) :
   """ Convert the message timestamp to local timezone.
       
       :param seconds : number of seconds
       :type seconds : int
       :returns date string for local timezone
      
   """     

   #Work in utc time, then convert to local time zone.    
   ts = datetime.fromtimestamp(seconds//1000)
   utc_ts = pytz.utc.localize(ts)
   #Finally convert to EST.
   est_ts = utc_ts.astimezone(pytz.timezone("America/New_York"))
   return(est_ts)
