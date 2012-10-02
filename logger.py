# -*- coding: utf-8 -*-
import sys, time

# Reference: http://goo.gl/6TBTI
class Logger:
  def __init__(self, io, filename, startStamp=True):
    self.io = io
    self.logfile = open(filename, 'a')
    self.logfile.write('\n\n======== New run at %s ========\n\n' % time.ctime() if startStamp else "")
  def write(self, text):
    self.io.write(text)
    self.logfile.write(text)
    self.logfile.flush()
  def close(self):
    self.io.close()
    self.logfile.close()

if __name__=='__main__':
  #Usage:
  sys.stdout = Logger(sys.stdout, 'running.log')
  sys.stderr = Logger(sys.stderr, 'running.log', startStamp=False)
  s = "Rock!"
  print '%s this should go on screen and in file' % s
  print 'this too'
  a = 2/0
  sys.stdout.close()
  sys.stderr.close()
