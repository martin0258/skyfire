# -*- coding: utf-8 -*-
import pyfire
import Skype4Py
import ConfigParser
import argparse
import os
import sys
import re
import skybot

class RoomCommand:
  AvailableCommands = \
  {
    r'\\topic$' : 'GetTopic',
    r'\\topic\s+\S' : 'SetTopic',
    r'\\who$' : 'GetUsers', 
    r'\\leave$' : 'LeaveRoom',
    r'\\help$' : 'ShowHelp'
  }
  def __init__(self, command, targetRoom, skypeUser):
    self.command = command
    self.targetRoom = targetRoom
    self.skypeUser = skypeUser
  """ para: self """
  def HandleCommand(self):
    for k, v in RoomCommand.AvailableCommands.items():
      if re.match(k, self.command):
        return getattr(self, v)()
    return "-- Sorry we don't implement this (bow)\n\\help for available commands"
  """ para: self """
  def GetTopic(self):
    return "topic=%s" % self.targetRoom.get_data()["topic"]
  """ para: self """
  def SetTopic(self):
    self.targetRoom.set_topic(self.command[6:].strip())
    return None
  """ para: self """
  def GetUsers(self):
    users = self.targetRoom.get_users()
    result = "-- Who's here?\n"
    for user in users:
      result += user["name"] + "\n"
    if len(users)==0:
      result += "No one is here...(tumbleweed)"
    return result
  """ para: self """
  def LeaveRoom(self):
    return "/kick %s" % self.skypeUser.Handle if self.targetRoom.leave() else "-- We don't know why, but %s failed to leave here" % self.skypeUser.DisplayName
  """ para: self """
  def ShowHelp(self):
    return "Available commands:\n" + \
           "\\topic\n" + \
           "\\topic NEW_TOPIC\n" + \
           "\\leave\n" + \
           "\\who\n" + \
           "\\help"

class NonRoomCommand:
  AvailableCommands = \
  {
    r'\\room$' : 'GetRoom',
    r'\\join\s+\S' : 'JoinRoom',
    r'\\help$' : 'ShowHelp'
  }
  def __init__(self, command, skypeUser):
    self.command = command
    self.skypeUser = skypeUser
  """ para: self """
  def HandleCommand(self):
    for k, v in NonRoomCommand.AvailableCommands.items():
      if re.match(k, self.command):
        return getattr(self, v)()
    return "Sorry we don't implement this (bow)\n\\help for available commands"
  """ para: self """
  def GetRoom(self):
    result = "-- Which room do you want to join?\n"
    for roomName in rooms:
      result += roomName + "\n"
    result += "No available room...(tumbleweed)" if len(rooms)==0 else "--\n\\join ROOM_NAME to join a room"
    return result
  """ para: self """
  def JoinRoom(self):
    global skype, rooms
    roomName = self.command[5:].strip()
    if roomName in rooms:
      #skype.CreateChatUsingBlob(rooms[roomName].blob).AddMembers(self.skypeUser)
      #skype.CreateChatUsingBlob(rooms[roomName].blob).SendMessage("/me")
      AddMemberCommand = "ALTER CHAT %s ADDMEMBERS %s" % (skype.CreateChatUsingBlob(rooms[roomName].blob).Name, self.skypeUser.Handle)
      Reply = "ALTER CHAT ADDMEMBERS"
      print AddMemberCommand, Reply
      skype.SendCommand(Skype4Py.api.Command(AddMemberCommand, Reply))
      result = "You should in the room now. Enjoy!" 
    else:
      result = "Sorry we don't have room [%s]...(bow)" % roomName
    return result
  """ para: self """
  def ShowHelp(self):
    return "Available commands:\n" + \
           "\\room\n" + \
           "\\join ROOM_NAME\n" + \
           "\\help"

class Skypefire:
  @staticmethod
  def getRoomBlob(room):
    """ para: Class Room in pyfire API """
    return rooms[Skypefire.getRoomName(room)].blob
  @staticmethod
  def getRoomName(room):
    """ para: Class Room in pyfire API """
    roomData = room.get_data()
    return roomData['name']
  @staticmethod
  def getRoomTopic(room):
    """ para: Class Room in pyfire API """
    roomData = room.get_data()
    return roomData['topic']
  @staticmethod
  def error(e):
    print("Stream STOPPED due to ERROR: %s" % e)
    print("Press ENTER to continue")
    
class CampfireEventHandler:
  @staticmethod
  def incoming(message):
    global skype, rooms
    msg = ""
    user = ""
    if message.user:
      user = message.user.name

    notDisplay = False
    if message.is_joining():
      msg = "--> %s ENTERS THE ROOM" % user
    elif message.is_leaving():
      msg = "<-- %s LEFT THE ROOM" % user
    elif message.is_tweet():
      msg = "[%s] %s TWEETED '%s' - %s" % (user, message.tweet["user"], message.tweet["tweet"], message.tweet["url"])
    elif message.is_text():
      msg = "%s" % (message.body)
    elif message.is_upload():
      msg = "-- %s UPLOADED FILE %s: %s" % (user, message.upload["name"],
      message.upload["url"])
    elif message.is_topic_change():
      msg = "-- %s CHANGED TOPIC TO '%s'" % (user, message.body)
    else:
      notDisplay = True

    roomName = Skypefire.getRoomName(message.room)
    roomBlob = Skypefire.getRoomBlob(message.room)
    if notDisplay:
      return
    if message.is_text() and user in rooms[roomName].msgFromSkype and message.body in rooms[roomName].msgFromSkype[user]:
      rooms[roomName].msgFromSkype[user].remove(message.body)
      rooms[roomName].latestSpeaker = user
      return
    if message.is_text():
      # Use skype chat command /me to specify who is speaking
      if user != rooms[roomName].latestSpeaker:
        skype.CreateChatUsingBlob(roomBlob).SendMessage("/me - [%s]" % user)
        rooms[roomName].latestSpeaker = user
      skype.CreateChatUsingBlob(roomBlob).SendMessage(msg)
      print msg
    if message.is_topic_change():
      rooms[roomName].topic = message.body
      skype.CreateChatUsingBlob(roomBlob).SendMessage(msg)
      print msg

class SkypeEventHandler:
  @staticmethod
  def monitor_message(msg, stat):
    global rooms, actionRooms, skype2camp
    msgBody = msg.Body.strip()
    print msg.Chat.Topic, stat, msg.FromHandle, msgBody
    msg.IsCommand = True if len(msgBody)>0 and msgBody[0] == '\\' else False
    if not stat == "RECEIVED":
      return
    if not msg.FromHandle in skype2camp:
      msg.Chat.SendMessage("-- Sorry you're not a member of skyfire service\nAsk admin to let you join the party\\0/")
    elif msg.Chat.Topic in rooms:
      roomName = msg.Chat.Topic
      if msg.IsCommand:
        result = RoomCommand(msgBody, actionRooms[msg.FromHandle][roomName], msg.Sender).HandleCommand()
        if result:
          skype.CreateChatUsingBlob(rooms[roomName].blob).SendMessage(result)
        return
      print "%s Sending to %s: %s" % (msg.FromHandle, roomName, msgBody)
      # The data structure used to avoid duplicate messages
      rooms[roomName].msgFromSkype[skype2camp[msg.FromHandle].campname].append(msgBody)
      actionRooms[msg.FromHandle][roomName].join()
      actionRooms[msg.FromHandle][roomName].speak(msgBody)
    else:
      # Non-room service. Let people join specifc room.
      if msg.IsCommand:
        result = NonRoomCommand(msgBody, msg.Sender).HandleCommand()
        if result:
          msg.Chat.SendMessage(result)
      else:
        msg.Chat.SendMessage(skybot.GetResponse(msgBody))

# main program
if __name__ == "__main__":
  # Change the working directory to the script's own directory
  # Purpose: run from python command line window in window task bar
  os.chdir(os.path.dirname(os.path.abspath(__file__)))

  description = "==========Use Skype as your amazing campfire client app=========="
  parser = argparse.ArgumentParser(description=description)
  parser.add_argument('-c', '--config', default='example.cfg', help='config file. Use [example.cfg] by default')
  parser.add_argument('-v', '--version', action='version', version='Skypefire 0.1')
  parser.add_argument('-l', '--logfile', help='log file. Print to stdout by default')
  args = parser.parse_args()

  rooms = {}
  actionRooms = {}
  skype2camp = {}
  config = ConfigParser.ConfigParser()
  config.optionxform = str
  config.read(args.config)
  domain = config.get('campfire','domain')
  username = config.get('campfire','username')
  password = config.get('campfire','password')
  campfire = pyfire.Campfire(domain, username, password, ssl=True)
  print 'Reading config file......'
  for item in config.items('blob'):
    print 'Get room [%s]' % item[0]
    rooms[item[0]] = campfire.get_room_by_name(item[0])
    rooms[item[0]].blob = item[1]
  for item in config.items('mapping'):
    print 'Get mapping [%s] -> [%s]' % (item[0], item[1])
    skype2camp[item[0]] = Skypefire()
    skype2camp[item[0]].token = item[1]

  skype = Skype4Py.Skype()
  skype.Attach()
  skype.OnMessageStatus = SkypeEventHandler.monitor_message
  if skype.CurrentUser.Handle in skype2camp:
    raw_input("Oops, got wrong skype instance: %s\nShould be someone else\nPress ENTER to exit..." % skype.CurrentUser.Handle)
    sys.exit(0)

  # TODO: We'll get SkypeError: [Errno 504] CHAT: action failed when using this (ALTER CHAT chatname SETOPTIONS 40)
  # Set skype chat room options in config file
  #for roomName in rooms:
  #  skype.CreateChatUsingBlob(rooms[roomName].blob).Options = 40

  """ multi-room version """
  for roomName in rooms:
    # msgFromSkype data structure: ['campfire user name'] -> ['msg1', 'msg2',..., 'msgn']
    rooms[roomName].msgFromSkype = {}
    rooms[roomName].topic = Skypefire.getRoomTopic(rooms[roomName])
    rooms[roomName].latestSpeaker = ""
    rooms[roomName].stream = rooms[roomName].get_stream(error_callback=Skypefire.error,live=False,use_process=False)
    rooms[roomName].stream.attach(CampfireEventHandler.incoming).start()
    print 'Listening for room [%s]...' % roomName

  """ multi-user action using skype """
  for skypename in skype2camp:
    actionRooms[skypename] = {}
    tempuser = campfire._user
    tempuser.token = skype2camp[skypename].token
    tempcamp = pyfire.Campfire(domain, username=None, password=None, ssl=True, currentUser=tempuser)
    skype2camp[skypename].campname = unicode(tempcamp.get_connection().get(url="users/me", key="user")["name"])
    print 'Skype:[%s] --> Campfire:[%s]' % (skypename, skype2camp[skypename].campname)
    for roomName in rooms:
      rooms[roomName].msgFromSkype[skype2camp[skypename].campname] = []
      actionRooms[skypename][roomName] = tempcamp.get_room_by_name(roomName)
      print 'Get action room [%s]' % roomName

  raw_input("Waiting for messages (Press ENTER to finish)\n")

  # Clean up
  for roomName in rooms:
    rooms[roomName].stream.stop().join()
    rooms[roomName].leave()
    print 'Leave room [%s]' % roomName
  for skypename in skype2camp:
    print 'Clean action rooms for [%s]' % skypename
    for roomName in actionRooms[skypename]:
      actionRooms[skypename][roomName].leave()
      print 'Leave action room [%s]' % roomName

  print 'Thank you for using skyfire! Bye=)'
  sys.exit(0)
