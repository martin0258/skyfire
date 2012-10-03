import Skype4Py, time
import win32com.client as comclt

# Create Skype instance
skype = Skype4Py.Skype()

# Connect Skype object to Skype client
skype.Attach()

print 'Your full name:', skype.CurrentUser.FullName
print 'Your contacts:'
for user in skype.Friends:
  print '    ', user.FullName

skype.Client.OpenMessageDialog('martin02588520')
#skype.Client.ButtonPressed('A')
#skype.Client.ButtonReleased('A')
wsh = comclt.Dispatch("WScript.Shell")
##wsh.AppActivate("Notepad") # select another application
for i in range(50):
  time.sleep(0.1)
  wsh.SendKeys(str(i)) # send the keys you want
