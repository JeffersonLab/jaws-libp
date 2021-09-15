""" 
.. module:: JAWSConnection
   :synopsis : Create JAWS kafka producers and consumers
   :notes : This module simplifies interaction with Kafka
.. moduleauthor::Michele Joyce <erb@jlab.org>
"""

import os
import pwd
import types
import pytz
import time

from datetime import datetime

# We can't use AvroProducer since it doesn't support string keys, see: https://github.com/confluentinc/confluent-kafka-python/issues/428

#  COMMON/GENERAL
from confluent_kafka.schema_registry import SchemaRegistryClient
from jlab_jaws.avro.subject_schemas.serde import ActiveAlarmSerde, \
   AlarmStateSerde, OverriddenAlarmValueSerde, RegisteredAlarmSerde, \
   OverriddenAlarmKeySerde

#  REGISTERED ALARMS
from jlab_jaws.avro.subject_schemas.serde import RegisteredAlarmSerde, \
   RegisteredClassSerde, RegisteredClassKeySerde   

from jlab_jaws.avro.subject_schemas.entities import RegisteredAlarm, RegisteredClass, RegisteredClassKey, \
    SimpleProducer, EPICSProducer, CALCProducer

from jlab_jaws.avro.referenced_schemas.entities import AlarmClass,\
   AlarmLocation, AlarmCategory, AlarmPriority




# OVERRIDDEN ALARMS
from jlab_jaws.avro.subject_schemas.entities import OverriddenAlarmValue, \
   LatchedAlarm, FilteredAlarm, MaskedAlarm, DisabledAlarm, OnDelayedAlarm,\
   OffDelayedAlarm, ShelvedAlarm, OverriddenAlarmKey, OverriddenAlarmType, \
   ShelvedAlarmReason

#  PRODUCER
from confluent_kafka import SerializingProducer
from confluent_kafka.serialization import StringSerializer, StringDeserializer

#  CONSUMER
from confluent_kafka.serialization import StringDeserializer
from jlab_jaws.eventsource.table import EventSourceTable



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


#Convert the timestamp into something readable
def get_msg_timestamp(msg) :
   """ Get timestamp of message
       
       :param msg : topic messge
       :type msg: 'cimpl.Message'
       :returns timestamp in local time zone
   """        
   #timestamp from Kafka is in UTC
   timestamp = msg.timestamp()
   return(convert_timestamp(timestamp[1]))

def get_headers(msg) :
   """ Get message headers
       
       :param msg : topic messge
       :type msg: 'cimpl.Message'
       :returns list of headers
   """           
   headers = msg.headers()
   return(headers)  
   
def get_msg_key(msg) :
   """ Get message key. 
       
       :param msg : topic messge
       :type msg: 'cimpl.Message'
       :returns key       
   """           
   return(msg.key())
 
def get_msg_value(msg) :
   """ Get message key. 
       
       :param msg : topic messge
       :type msg: 'cimpl.Message'
       :returns value object      
   """           
   return(msg.value())

def get_msg_topic(msg) :
   """ Get message topic
       
       :param msg : topic messge
       :type msg: 'cimpl.Message'
       :returns topic     
   """           
   return(msg.topic())   

def get_alarm_class_list() :
   """ Get list of valid alarm class names 
       
       :returns list AlarmClass member names
   """  
   return(AlarmClass._member_names_)
   
def get_location_list() :
   """ Get list of valid locations
       
       :returns list AlarmLocation member names       
   """     
   return(AlarmLocation._member_names_)
   
def get_category_list() :
   """ Get list of valid categories
       
       :returns list AlarmCategory member names
   """    
   return(AlarmCategory._member_names_)

def get_priority_list() :
   """ Get list of valid priorities
       
       :returns list AlarmPriority member names
   """     
   return(AlarmPriority._member_names_)

def get_override_reasons() :
   return(ShelvedAlarmReason._member_names_)
   
class JAWSConnection(object) :
   """ This class sets up the kafka connection for creating consumers and
       producers
   """
   def __init__(self,topic) :
      """ Create a kafkaconnection for the topic
       
       :param topic: Name of topic
       :type topic: string
      
      """           
      self.topic = topic
      
      #Magic Kafka configuration
      bootstrap_servers = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')
      self.bootstrap_servers = bootstrap_servers
      
      conf = {'url': os.environ.get('SCHEMA_REGISTRY', 'http://localhost:8081')}
      self.schema_registry = SchemaRegistryClient(conf)
      self.params = types.SimpleNamespace()
      
      self.key_deserializer = StringDeserializer('utf_8')
      self.key_serializer = StringSerializer()

      #Initialize connections 
      
      self.avro_serdes = {
         'registered-alarms' : {
            'serde' : RegisteredAlarmSerde,
            'deserializer' : None,
            'serializer'   : None
         },
         'active-alarms'     : {
            'serde' : ActiveAlarmSerde,
            'deserializer' : None,
            'serializer'   : None
         },
         'alarm-state' : {
            'serde' : AlarmStateSerde,
            'deserializer' : None,
            'serializer'   : None
         }
         #'overridden-alarms' : OverriddenAlarmSerde
      }


      
         


class JAWSProducer(JAWSConnection) :
   """ JAWSConnection that PRODUCES and sends messages 
       
   """
   #NOTE: Most of this has been stolen from Ryan's examples
   def __init__(self,managername,topic) :
      """ Create a JAWSProducer instance
          
          :param topic: Name of topic
          :type topic: string
          :param name: name of producer
          :type name: string
      """
      super(JAWSProducer,self).__init__(topic)

      topic = self.topic
            
      self.hdrs = [('user', pwd.getpwuid(os.getuid()).pw_name),
         ('producer',managername),('host',os.uname().nodename)]

   def _create_producer(self) :
      config = None
           
      producer_config = {
                'bootstrap.servers'  : self.bootstrap_servers,
                'key.serializer'   : self.key_serializer,
                'value.serializer' : self.value_serializer,
                
               }
      producer = SerializingProducer(producer_config)
      return(producer)
      
      
   def send_message(self,params) :
      """ Send a message to a topic 
          :param params: message content
          :type params: types.SimpleNamespace()
          
          params must include:
            params.key (name of alarm)
            params.topic (topic to send message)
            params.value
            
      """
      
      producer = self.producer 
      
      producer.produce(topic=params.topic,value=params.value,key=params.key,
         headers=self.hdrs,on_delivery=self.delivery_report)
      producer.flush()
   
      

   #Create an acknowledge message
   def ack_message(self,name) :
      """ Create an acknowledgement message
          
          :param name: name of alarm
          :type name: string
  
      """
      #Build the message to pass to producer. 
      params = types.SimpleNamespace()
      params.value = None
      params.key = name
      params.topic = self.topic
      
      ### FOR TESTING PURPOSES ###
      ### Until active-alarms/alarm-state/latching works
      #params.value = AlarmStateValue(AlarmStateEnum['Active'])
      #print("VAL",params.value)
      #return
      #params.topic = "alarm-state"
      
      self.send_message(params)

   #Report success or errors
   def delivery_report(self,err, msg):
      
    """ Called once for each message produced to indicate delivery result.
        Triggered by poll() or flush(). """
    if err is not None:
        print('Message delivery failed: {}'.format(err))
    else:
        print('Message delivered')
   

   
class OverrideProducer(JAWSProducer) :
   def __init__(self,managername,overridetype) :
      
      super(OverrideProducer,self).__init__(managername,'overridden-alarms')
      self.topic = 'overridden-alarms'
      self.key_serializer = \
         OverriddenAlarmKeySerde.serializer(self.schema_registry)
      self.value_serializer = \
         OverriddenAlarmValueSerde.serializer(self.schema_registry)
      
      
      self.overridetype = OverriddenAlarmType[overridetype]
      self.params = types.SimpleNamespace()
      
      self.params.topic = self.topic
      
      self.producer = self._create_producer()
    
   def disable_message(self,name,comment) :
      
      self.params.key = OverriddenAlarmKey(name,self.overridetype)
      msg = DisabledAlarm(comment)
      self.params.value = OverriddenAlarmValue(msg)
      self.send_message()
     
  
  
   def oneshot_message(self,name,reason,comments) :
      """ Create OneShot shelving message        
          :param name: name of alarm
          :type name: string
  
      """
      self.params.key = OverriddenAlarmKey(name,self.overridetype)
      msg = ShelvedAlarm(1,comments,ShelvedAlarmReason[reason],True)
      self.params.value = OverriddenAlarmValue(msg)
      self.send_message()
   
   def shelve_message(self,name,expseconds,reason,comments=None) :
      print("NAME:",name,"SEC:",expseconds,"RE",reason,"COMMENTS:",comments)
      
      now = int(time.time())
      timestampseconds  = now + expseconds
      
      timestampmillies = int(timestampseconds * 1000)
      
      
      
      self.params.key = OverriddenAlarmKey(name,self.overridetype)
      msg = ShelvedAlarm(timestampmillies,comments,ShelvedAlarmReason[reason],False)
      self.params.value = OverriddenAlarmValue(msg)
      
      self.send_message()
      
      
   #Create an acknowledge message
   def ack_message(self,name) :
      """ Create an acknowledgement message
          
          :param name: name of alarm
          :type name: string
  
      """
      
      self.params.key = OverriddenAlarmKey(name,self.overridetype)
      #Build the message to pass to producer. 
     # params = types.SimpleNamespace()
      self.params.value = None
      
      self.send_message()
      return
      
      
      #params.key = name
      #params.topic = self.topic
      
      ### FOR TESTING PURPOSES ###
      ### Until active-alarms/alarm-state/latching works
      #params.value = AlarmStateValue(AlarmStateEnum['Active'])
      #print("VAL",params.value)
      #return
      #params.topic = "alarm-state"
      
      self.send_message(params)
   
   def send_message(self) :
         
      params = self.params
      
     # print("MSG:",params.value)
      #self.producer = SerializingProducer(producer_config)
      #self.send_message(params)
      producer = self.producer 
      
      producer.produce(topic=params.topic,value=params.value,key=params.key,
         headers=self.hdrs,on_delivery=self.delivery_report)
      producer.flush()




class JAWSConsumer(JAWSConnection) :
   """ JAWSConnection that subscribes to topics and consumes messages 
   """
   
   def __init__(self,topic,init_state,update_state,name,
      monitor=True) :
      
      """ Create a JAWSConsumer instance
          
          :param topic: Name of topic
          :type topic: string
          :param init_state: Callback providing initial state
          :type init_state: (callable(dict))
          :param update_state: Callback providing updated state
          :type update_state: (callable(dict))
          :param name: Name of consumer
          :type name: string
          :param monitor : Continue monitoring
          :type monitor: boolean
      """
            
      super(JAWSConsumer,self).__init__(topic)
      
      self.name = name
      self.topic = topic
      self.monitor = monitor
      self.init_state = init_state
      self.update_state = update_state
      
   def _create_event_table(self) :
      ts = time.time()
      print("***<",self.name,">") # + str(ts))
      consumer_config = {
         'topic': self.topic,
         'monitor' : self.monitor,
         'bootstrap.servers'  : self.bootstrap_servers,
         'key.deserializer'   : self.key_deserializer,
         'value.deserializer' : self.value_deserializer,
         'group.id' : self.name + " " + str(ts)
      }
      
      self.event_table = \
         EventSourceTable(consumer_config,self.init_state,self.update_state)
  
   def start(self) :
      """ Start the event_table monitoring
      """
      
      self.event_table.start()
                
   def stop(self) :
      """ Stop the event_table
      """
      self.event_table.stop()

class AlarmStateConsumer(JAWSConsumer) :
   def __init__(self,init_state,update_state,name,monitor=True) :
      super(AlarmStateConsumer,self).__init__('alarm-state',
         init_state,update_state,name, monitor)
      
      self.key_deserializer = StringDeserializer()
      self.value_deserializer = \
         AlarmStateSerde.deserializer(self.schema_registry)
         
      self._create_event_table()
      
class RegisteredAlarmsConsumer(JAWSConsumer) :
   def __init__(self,init_state,update_state,name,monitor=True) :
      super(RegisteredAlarmsConsumer,self).__init__('registered-alarms',
         init_state,update_state,name, monitor)
      
      self.key_deserializer = StringDeserializer('utf_8')
      self.value_deserializer = \
          RegisteredAlarmSerde.deserializer(self.schema_registry)
      
      self.classes_key_deserializer = \
         RegisteredClassKeySerde.deserializer(self.schema_registry) 
      
      self.classes_value_deserializer = \
         RegisteredClassSerde.deserializer(self.schema_registry)

      self._create_event_table()

class ActiveAlarmsConsumer(JAWSConsumer) :
   def __init__(self,init_state,update_state,name,monitor=True) :
      
      super(ActiveAlarmsConsumer,self).__init__('active-alarms',
         init_state,update_state,name, monitor)
      
      self.key_deserializer = StringDeserializer()
      self.value_deserializer = \
         ActiveAlarmSerde.deserializer(self.schema_registry)

      self._create_event_table()
      
