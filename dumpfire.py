# -*- coding: utf-8 -*-
import pyfire
import ConfigParser
import argparse
import datetime
import sys
import codecs

# main program
if __name__ == '__main__':
  # Fix decode error when using window I/O redirect
  sys.stdout = codecs.getwriter('utf-8')(sys.stdout)
  description = '==========Dump transcript from campfire room=========='
  parser = argparse.ArgumentParser(description=description)
  parser.add_argument('-c', '--config', default='example.cfg', help='config file. Use [example.cfg] by default')
  parser.add_argument('-v', '--version', action='version', version='dumpfire 0.1')
  args = parser.parse_args()

  rooms = {}
  config = ConfigParser.ConfigParser()
  config.optionxform = str
  config.read(args.config)
  domain = config.get('campfire','domain')
  username = config.get('campfire','username')
  password = config.get('campfire','password')
  skypename = config.get('campfire','skypename')
  campfire = pyfire.Campfire(domain, username, password, ssl=True)

  """ multi-room version """
  for item in config.items('transcript'):
    roomName = item[0]
    try:
      time = datetime.datetime.strptime(item[1], '%Y-%m-%d')
    except ValueError:
      time = datetime.date.today()
    print '===== Getting transcript from room [', roomName, '] from ', time, ' ====='
    rooms[roomName] = campfire.get_room_by_name(roomName)
    messages = rooms[roomName].transcript(time)
    for message in messages:
      if message.user:
        user = message.user.name
      if message.is_text():
        print "[%s] [%s] %s" % (message.get_data()['created_at'], user, message.body)
    print '===== End of room [', roomName, '] =====\n'

  sys.stderr.write('Thank you for using dumpfire! Bye=)\n')
