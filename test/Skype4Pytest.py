import Skype4Py, time, sys, platform

"""
Main purpose of (2)(3)(4) is about typing indicator.
Test case:
  1. Attach running Skype
  2. OpenMessageDialog
  3. Type somethings
  4. Close Message Dialog
"""
if __name__ == "__main__":
 osPlatform = platform.system()
  print 'Your platform is %s' % osPlatform
  if osPlatform=="Windows":
    import win32com.client as comclt
  elif osPlatform=="Linux":
    import uinput
  else:
    print 'Sorry your we do not have implementation on %s' % osPlatform
    sys.exit(0)

  # Create Skype instance
  skype = Skype4Py.Skype(Transport='x11') if osPlatform=="Linux" else Skype4Py.Skype()

  # (1) Connect Skype object to Skype client
  skype.Attach()

  print 'Your full name:', skype.CurrentUser.FullName
  print 'Your contacts:'
  for user in skype.Friends:
    print '    ', user.FullName

  # (2)
  skype.Client.OpenMessageDialog('echo123')
  if osPlatform=="Windows":
    wsh = comclt.Dispatch("WScript.Shell")
    wsh.SendKeys('...') # send the keys you want
  elif osPlatform=="Linux":
    # Check /usr/include/linux/input.h for more definitions
    events = (uinput.KEY_DOT, uinput.KEY_LEFTALT, uinput.KEY_F4)
    device = uinput.Device(events)
    # (3)
    device.emit(uinput.KEY_DOT, 1)
    device.emit(uinput.KEY_DOT, 0)
    device.emit(uinput.KEY_BACKSPACE, 1)
    device.emit(uinput.KEY_BACKSPACE, 0)
    # (4)
    device.emit(uinput.KEY_LEFTALT, 1)
    device.emit(uinput.KEY_F4, 1)
    device.emit(uinput.KEY_F4, 0)
    device.emit(uinput.KEY_LEFTALT, 0)
    time.sleep(3) # we need this to let input completetly be sent to kernel
  else:
    # Should never reach here
    pass
