# -*- coding: utf-8 -*-
import pyfire
import Skype4Py
import ConfigParser
import argparse
import os
import sys
import re
import skybot

class UserCommand:
  AvailableCommands = {}
  def HandleCommand(self):
    for k, v in self.__class__.AvailableCommands.items():
      if re.match(k, self.command):
        return getattr(self, v)()
    return "-- Sorry we don't implement this (bow)\n\\help for available commands"

class RoomCommand(UserCommand):
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

class NonRoomCommand(UserCommand):
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
  def GetRoom(self):
    global campfires
    result = "-- Room List\n"
    roomList = Skyfire.GetRoomList(self.skypeUser)
    for roomName in roomList:
      result += "[%s]\n" % roomName
    result += "No available room...(tumbleweed)" if len(roomList)==0 else ""
    return result
  """ para: self """
  def JoinRoom(self):
    global skype, campfires
    roomName = self.command[5:].strip()
    if roomName in Skyfire.GetRoomList(self.skypeUser):
      # ERROR: we would get unexpected return using the method of following line
      #skype.CreateChatUsingBlob(rooms[roomName].blob).AddMembers(self.skypeUser)
      if campfires[self.skypeUser.Handle].get_room_by_name(roomName).join():
        AddMemberCommand = "ALTER CHAT %s ADDMEMBERS %s" % (skype.CreateChatUsingBlob(rooms[roomName].blob).Name, self.skypeUser.Handle)
        Reply = "ALTER CHAT ADDMEMBERS"
        skype.SendCommand(Skype4Py.api.Command(AddMemberCommand, Reply))
        result = "You should in the room now. Enjoy!"
      else:
        result = "You failed to join the room. Sorry (bow)"
    else:
      result = "Sorry room [%s] is not in the list (bow)" % roomName
    return result
  """ para: self """
  def ShowHelp(self):
    return "Available commands:\n" + \
           "\\room\n" + \
           "\\join ROOM_NAME\n" + \
           "\\help"

class Skyfire:
  """ para: Skype4Py User Object """
  @staticmethod
  def GetRoomList(skypeUser):
    return [room['name'] for room in campfires[skypeUser.Handle].get_rooms()] if skypeUser.Handle in campfires else []
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

    roomName = message.room.get_data()['name']
    roomBlob = rooms[roomName].blob
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
    elif message.is_topic_change():
      rooms[roomName].topic = message.body
      skype.CreateChatUsingBlob(roomBlob).SendMessage(msg)
      print msg
    else:
      # We're not going to deal with other types
      pass

class SkypeEventHandler:
  @staticmethod
  def monitor_message(msg, stat):
    global rooms, campfires, skype2camp
    msgBody = msg.Body.strip()
    print msg.Chat.Topic, stat, msg.FromHandle, msgBody
    msg.IsCommand = True if len(msgBody)>0 and msgBody[0] == '\\' else False
    if not stat == "RECEIVED":
      return
    if not msg.FromHandle in skype2camp:
      msg.Chat.SendMessage("Sorry you're not a member of skyfire service\nAsk admin to let you in.")
    elif msg.Chat.Topic in Skyfire.GetRoomList(msg.Sender):
      roomName = msg.Chat.Topic
      targetRoom = campfires[msg.FromHandle].get_room_by_name(roomName)
      if msg.IsCommand:
        result = RoomCommand(msgBody, targetRoom, msg.Sender).HandleCommand()
        if result:
          skype.CreateChatUsingBlob(rooms[roomName].blob).SendMessage(result)
        return
      print "%s Sending to %s: %s" % (msg.FromHandle, roomName, msgBody)
      # The data structure used to avoid duplicate messages
      rooms[roomName].msgFromSkype[skype2camp[msg.FromHandle].campname].append(msgBody)
      targetRoom.join()
      targetRoom.speak(msgBody)
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

  description = "========== Use Skype as your amazing campfire client app =========="
  parser = argparse.ArgumentParser(description=description)
  parser.add_argument('-c', '--config', default='example.cfg', help='config file. Use [example.cfg] by default')
  parser.add_argument('-v', '--version', action='version', version='Skyfire 0.1')
  parser.add_argument('-l', '--logfile', help='log file. Print to stdout by default')
  parser.add_argument('--test', action="store_true", help="Only room's name starts with 'Test' would be listened.")
  args = parser.parse_args()

  rooms = {}
  skype2camp = {}
  campfires = {}
  config = ConfigParser.ConfigParser()
  config.optionxform = str
  config.read(args.config)
  domain = config.get('campfire','domain')
  username = config.get('campfire','username')
  password = config.get('campfire','password')
  campfire = pyfire.Campfire(domain, username, password, ssl=True)
  print 'Reading config file......'
  for item in config.items('mapping'):
    print 'Get mapping [%s] -> [%s]' % (item[0], item[1])
    skype2camp[item[0]] = Skyfire()
    skype2camp[item[0]].token = item[1]

  skype = Skype4Py.Skype()
  skype.Attach()
  skype.OnMessageStatus = SkypeEventHandler.monitor_message
  if skype.CurrentUser.Handle in skype2camp:
    raw_input("Oops, got wrong skype instance: %s\nShould be someone else\nPress ENTER to exit..." % skype.CurrentUser.Handle)
    sys.exit(0)
  assert skype.CurrentUser.OnlineStatus=='INVISIBLE', 'Please keep bot invisible until it totally awake.'

  # TODO: We'll get SkypeError: [Errno 504] CHAT: action failed when using this (ALTER CHAT chatname SETOPTIONS 40)
  # Set skype chat room options in config file
  #for roomName in rooms:
  #  skype.CreateChatUsingBlob(rooms[roomName].blob).Options = 40

  for skypename in skype2camp:
    tempuser = campfire._user
    tempuser.token = skype2camp[skypename].token
    tempcamp = pyfire.Campfire(domain, username=None, password=None, ssl=True, currentUser=tempuser)
    campfires[skypename] = tempcamp
    skype2camp[skypename].campname = unicode(tempcamp.get_connection().get(url="users/me", key="user")["name"])
    print 'Skype:[%s] --> Campfire:[%s]' % (skypename, skype2camp[skypename].campname)
    for roomName in Skyfire.GetRoomList(skype.User(skypename)):
      if args.test and roomName.find('Test')!=0:
        continue
      # Initialize room for listening message from campfire
      if not roomName in rooms:
        rooms[roomName] = tempcamp.get_room_by_name(roomName)
        rooms[roomName].blob = config.get('blob',roomName)
        # msgFromSkype data structure: ['campfire user name'] -> ['msg1', 'msg2',..., 'msgn']
        rooms[roomName].msgFromSkype = {}
        rooms[roomName].msgFromSkype[skype2camp[skypename].campname] = []
        rooms[roomName].topic = rooms[roomName].get_data()['topic']
        rooms[roomName].latestSpeaker = ""
        rooms[roomName].stream = rooms[roomName].get_stream(error_callback=Skyfire.error,live=False,use_process=False)
        rooms[roomName].stream.attach(CampfireEventHandler.incoming).start()
        print 'Listening for room [%s]...' % roomName

  skype.ChangeUserStatus('ONLINE')
  raw_input("Waiting for messages (Press ENTER to finish)\n")
  skype.ChangeUserStatus('INVISIBLE')

  # Clean up
  for roomName in rooms:
    rooms[roomName].stream.stop().join()
    rooms[roomName].leave()
    print 'Leave room [%s]' % roomName

  print 'Thank you for using skyfire! Bye=)'
  sys.exit(0)
