# -*- coding: utf-8 -*-
import pyfire
import Skype4Py
import ConfigParser
import argparse
import os
import platform
import sys
import re
import skybot
import logger
import win32com.client as comclt

class Skyfire:
  """ para: Skype4Py User Object """
  @staticmethod
  def GetRoomList(skypeUser):
    global skyfirers
    roomList = [room['name'] for room in skyfirers[skypeUser.Handle].campObj.get_rooms()] if skypeUser.Handle in skyfirers else []
    return [roomName for roomName in roomList if roomName.find('Test')==0] if args.test else roomList
  @staticmethod
  def GetSkypeNameByCampId(campId):
    """
    Args: campId (str):  campfire user Id.
    Returns: skypename(str) or None if not found.
    """
    global skyfirers
    skypename = [skypename for skypename in skyfirers if hasattr(skyfirers[skypename], 'campId') and skyfirers[skypename].campId==campId ]
    return skypename[0] if len(skypename)>0 else None
  @staticmethod
  def OpenChatByName(chatname):
    global skype
    OpenChatCommand = "OPEN CHAT %s" % (chatname)
    Reply = OpenChatCommand
    skype.SendCommand(Skype4Py.api.Command(OpenChatCommand, Reply))
  @staticmethod
  def EmulateTyping():
    global wsh
    platform = platform.system()
    if platform=="Windows":
      wsh.SendKeys('...')
    elif platform=="Linux":
      events = (uinput.KEY_DOT, uinput.KEY_BACKSPACE)
      device = uinput.Device(events)
      device.emit(uinput.KEY_DOT, 1)
      device.emit(uinput.KEY_DOT, 0)
      device.emit(uinput.KEY_BACKSPACE, 1)
      device.emit(uinput.KEY_BACKSPACE, 0)
    else:
      pass
  @staticmethod
  def error(e):
    print("Stream STOPPED due to ERROR: %s" % e)
    print("Press ENTER to continue")
    
class UserCommand:
  AvailableCommands = {}
  def HandleCommand(self):
    for k, v in self.__class__.AvailableCommands.items():
      if re.match(k, self.command):
        return getattr(self, v)()
    return "-- Sorry we don't implement this.\n\\help for available commands"

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
    result = "-- Room List\n"
    roomList = Skyfire.GetRoomList(self.skypeUser)
    for roomName in roomList:
      result += "[%s]\n" % roomName
    result += "No available room...(tumbleweed)" if len(roomList)==0 else ""
    return result
  """ para: self """
  def JoinRoom(self):
    global skype, skyfirers
    roomName = self.command[5:].strip()
    if roomName in Skyfire.GetRoomList(self.skypeUser):
      # ERROR: we would get unexpected return using the method of following line
      #skype.CreateChatUsingBlob(rooms[roomName].blob).AddMembers(self.skypeUser)
      if skyfirers[self.skypeUser.Handle].campObj.get_room_by_name(roomName).join():
        AddMemberCommand = "ALTER CHAT %s ADDMEMBERS %s" % (skype.CreateChatUsingBlob(rooms[roomName].blob).Name, self.skypeUser.Handle)
        Reply = "ALTER CHAT ADDMEMBERS"
        skype.SendCommand(Skype4Py.api.Command(AddMemberCommand, Reply))
        result = "You should be in the room now. Enjoy!"
      else:
        result = "Sorry but you failed to join the room."
    else:
      result = "Sorry [%s] is not in the room list." % roomName
    return result
  """ para: self """
  def ShowHelp(self):
    return "Available commands:\n" + \
           "\\room\n" + \
           "\\join ROOM_NAME\n" + \
           "\\help"

class CampfireEventHandler:
  @staticmethod
  def incoming(message):
    global skype, rooms, skyfirers
    msg = ""
    campName = ""
    if message.user:
      campName = message.user.name
      campId = message.user.id

    notDisplay = False
    if message.is_joining():
      msg = "--> %s ENTERS THE ROOM" % campName
    elif message.is_leaving():
      msg = "<-- %s LEFT THE ROOM" % campName
    elif message.is_tweet():
      msg = "[%s] %s TWEETED '%s' - %s" % (campName, message.tweet["user"], message.tweet["tweet"], message.tweet["url"])
    elif message.is_text():
      msg = "%s" % (message.body)
    elif message.is_upload():
      msg = "-- %s UPLOADED FILE %s: %s" % (campName, message.upload["name"],
      message.upload["url"])
    elif message.is_topic_change():
      msg = "-- %s CHANGED TOPIC TO '%s'" % (campName, message.body)
    else:
      notDisplay = True

    roomName = message.room.get_data()['name']
    roomBlob = rooms[roomName].blob
    if notDisplay:
      return
    if message.is_text() and campId in rooms[roomName].msgFromSkype and message.body in rooms[roomName].msgFromSkype[campId]:
      rooms[roomName].msgFromSkype[campId].remove(message.body)
      rooms[roomName].latestSpeaker = campId
      return
    if message.is_text():
      # Use skype chat command /me to specify who is speaking
      if campId != rooms[roomName].latestSpeaker:
        skype.CreateChatUsingBlob(roomBlob).SendMessage("/me - [%s]" % campName)
        rooms[roomName].latestSpeaker = campId
      skype.CreateChatUsingBlob(roomBlob).SendMessage(msg)
      print msg
    elif message.is_topic_change():
      rooms[roomName].topic = message.body
      skype.CreateChatUsingBlob(roomBlob).SendMessage(msg)
      print msg
    elif message.is_leaving():
      # Keep you in the room if you're in the corresponding skype group chat
      skypename = Skyfire.GetSkypeNameByCampId(campId)
      if skypename and skypename in [member.Handle for member in skype.CreateChatUsingBlob(roomBlob).Members]:
        skyfirers[skypename].campObj.get_room_by_name(roomName).join()
        print 'rejoin %s to %s' % (skypename, roomName)
    else:
      # We're not going to deal with other types
      pass

class SkypeEventHandler:
  @staticmethod
  def monitor_message(msg, stat):
    global rooms, skyfirers
    msgBody = msg.Body.strip()
    msg.IsCommand = True if len(msgBody)>0 and msgBody[0] == '\\' else False
    print msg.Chat.Topic, stat, msg.FromHandle, msgBody
    if not stat == "RECEIVED":
      return
    if not msg.FromHandle in skyfirers:
      msg.Chat.SendMessage("Sorry you're not a member of skyfire service\nAsk admin to let you in.")
    elif msg.Chat.Topic in Skyfire.GetRoomList(msg.Sender):
      roomName = msg.Chat.Topic
      targetRoom = skyfirers[msg.FromHandle].campObj.get_room_by_name(roomName)
      if msg.IsCommand:
        result = RoomCommand(msgBody, targetRoom, msg.Sender).HandleCommand()
        if result:
          skype.CreateChatUsingBlob(rooms[roomName].blob).SendMessage(result)
        return
      print "%s Sending to %s: %s" % (msg.FromHandle, roomName, msgBody)
      rooms[roomName].msgFromSkype[skyfirers[msg.FromHandle].campId].append(msgBody)
      targetRoom.join()
      targetRoom.speak(msgBody)
    else:
      Skyfire.OpenChatByName(msg.Chat.Name)
      Skyfire.EmulateTyping()
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
  parser.add_argument('-l', '--logfile', default='running.log', help='log file. Use [running.log] by default')
  parser.add_argument('-t', '--test', action="store_true", help="Only room that its name begins with 'Test' would be used.")
  args = parser.parse_args()

  sys.stdout = logger.Logger(sys.stdout, args.logfile)
  sys.stderr = logger.Logger(sys.stderr, args.logfile, startStamp=False)
  # data structure to store users' info who are using this integration service
  # ['skypename'] : Skyfire object, which contains token, campfire object, campfire userId
  skyfirers = {}
  rooms = {}
  print 'Reading config file......'
  config = ConfigParser.ConfigParser()
  config.optionxform = str
  config.read(args.config)
  platform = platform.system()
  Skype4PyInterface = config.get('Skype4Py','interface')
  domain = config.get('campfire','domain')
  username = config.get('campfire','username')
  password = config.get('campfire','password')
  campfire = pyfire.Campfire(domain, username, password, ssl=True)
  for item in config.items('mapping'):
    print 'Get mapping [%s] -> [%s]' % (item[0], item[1])
    skyfirers[item[0]] = Skyfire()
    skyfirers[item[0]].token = item[1]

  # Initialize the com we would use to send keys
  if platform=="Windows":
    wsh = comclt.Dispatch("WScript.Shell")
  skype = Skype4Py.Skype(Transport=Skype4PyInterface) if platform=="Linux" else Skype4Py.Skype()
  skype.Attach()
  skype.OnMessageStatus = SkypeEventHandler.monitor_message
  if skype.CurrentUser.Handle in skyfirers:
    raw_input("Oops, got wrong skype instance: %s\nShould be someone else\nPress ENTER to exit..." % skype.CurrentUser.Handle)
    sys.exit(0)
  assert skype.CurrentUser.OnlineStatus=='INVISIBLE', 'Please keep bot invisible until it totally awake.'

  # TODO: We'll get SkypeError: [Errno 504] CHAT: action failed when using this (ALTER CHAT chatname SETOPTIONS 40)
  # Currently we could only set necessary chat options manually
  # Set skype chat room options in config file
  #for roomName in rooms:
  #  skype.CreateChatUsingBlob(rooms[roomName].blob).Options = 40

  for skypename in skyfirers:
    tempuser = campfire._user
    tempuser.token = skyfirers[skypename].token
    tempcamp = pyfire.Campfire(domain, username=None, password=None, ssl=True, currentUser=tempuser)
    skyfirers[skypename].campObj = tempcamp
    skyfirers[skypename].campId = tempcamp.get_connection().get(url="users/me", key="user")["id"]
    campUsername = unicode(tempcamp.get_connection().get(url="users/me", key="user")["name"])
    print 'Skype:[%s] --> Campfire:[%s]' % (skypename, campUsername)
    for roomName in Skyfire.GetRoomList(skype.User(skypename)):
      # Initialize room for listening message from campfire
      if not roomName in rooms:
        rooms[roomName] = tempcamp.get_room_by_name(roomName)
        rooms[roomName].blob = config.get('blob',roomName)
        # msgFromSkype is the data structure used to avoid duplicate message: [campfire userId] -> ['msg1', 'msg2',..., 'msgn']
        rooms[roomName].msgFromSkype = {}
        rooms[roomName].topic = rooms[roomName].get_data()['topic']
        rooms[roomName].latestSpeaker = None
        rooms[roomName].stream = rooms[roomName].get_stream(error_callback=Skyfire.error,live=False,use_process=False)
        rooms[roomName].stream.attach(CampfireEventHandler.incoming).start()
        print 'Listening for room [%s]...' % roomName
      rooms[roomName].msgFromSkype[skyfirers[skypename].campId] = []

  skype.ChangeUserStatus('ONLINE')
  raw_input("Waiting for messages (Press ENTER to finish)\n")
  skype.ChangeUserStatus('INVISIBLE')

  # Clean up
  for roomName in rooms:
    rooms[roomName].stream.stop().join()
    print 'Clean up room [%s]' % roomName

  print 'Thank you for using skyfire! Bye=)'
  sys.stdout.close()
  sys.stderr.close()
  sys.exit(0)
