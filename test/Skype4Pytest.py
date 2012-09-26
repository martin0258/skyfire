import Skype4Py

# Create Skype instance
skype = Skype4Py.Skype()

# Connect Skype object to Skype client
skype.Attach()

print 'Your full name:', skype.CurrentUser.FullName
print 'Your contacts:'
for user in skype.Friends:
    print '    ', user.FullName