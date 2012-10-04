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
  print 'Your Skype name:', skype.CurrentUserHandle
 
  # (2)
  time.sleep(3)
  skype.CreateChatWith('skysourcefire').OpenWindow()
  # Following method would get Skype4Py.errors.SkypeError: [Errno 7] in Ubuntu 12.04
  # skype.Client.OpenMessageDialog('echo123')
  if osPlatform=="Windows":
    wsh = comclt.Dispatch("WScript.Shell")
    wsh.SendKeys('..................') # trigger typing indicator
    time.sleep(3) # If you close the window too quick, you'll not see the typing indicator
    wsh.SendKeys('^a{DEL}%{F4}') # clear text and close chat window
  elif osPlatform=="Linux":
    # Pre-Condition: sudo apt-get install xdotool
    windowId = subprocess.check_output(['xdotool', 'getactivewindow'])
    windowName = subprocess.check_output(['xdotool', 'getwindowname', windowId ])
    assert "Skype" in windowName, "Wrong focus window [%s]. Should be Skype." % windowName
    subprocess.check_output(['xdotool', 'key', 'a', 'ctrl+a', 'BackSpace', 'alt+F4'])
    # Check /usr/include/linux/input.h for more definitions
    # Note: You may need to 'sudo' if you get 'OSError: [Errno 13] Permission denied'
    # TODO: The following method only works sometimes. Don't know why.
    #events = (uinput.KEY_H, uinput.KEY_LEFTALT, uinput.KEY_F4)
    #device = uinput.Device(events)
    #device.emit(uinput.KEY_H, 1)
    #device.emit(uinput.KEY_H, 0)
    #device.emit(uinput.KEY_LEFTALT, 1)
    #device.emit(uinput.KEY_F4, 1)
    #device.emit(uinput.KEY_F4, 0)
    #device.emit(uinput.KEY_LEFTALT, 0)
  else:
    # Should never reach here
    pass
