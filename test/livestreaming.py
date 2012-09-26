import pyfire
  def monitor_message(

def incoming(message):
    user = ""
    if message.user:
        user = message.user.name

    if message.is_joining():
        print "--> %s ENTERS THE ROOM" % user
    elif message.is_leaving():
        print "<-- %s LEFT THE ROOM" % user
    elif message.is_tweet():
        print "[%s] %s TWEETED '%s' - %s" % (user, message.tweet["user"], 
            message.tweet["tweet"], message.tweet["url"])
    elif message.is_text():
        print "[%s] %s" % (user, message.body)
    elif message.is_upload():
        print "-- %s UPLOADED FILE %s: %s" % (user, message.upload["name"],
            message.upload["url"])
    elif message.is_topic_change():
        print "-- %s CHANGED TOPIC TO '%s'" % (user, message.body)

def error(e):
    print("Stream STOPPED due to ERROR: %s" % e)
    print("Press ENTER to continue")

campfire = pyfire.Campfire("skysourcer", "martin.ku@skysource.com.tw", "abcd1234!", ssl=True)
#room = campfire.get_room_by_name("Test for skypefire")
stream = campfire.get_room_by_name("Test for skypefire").get_stream(live=False,use_process=False)
stream = room.get_stream(live=False,use_process=False,error_callback=error)

#live=True cannot work unfortuately...(which mean live streaming does not work well)
#use_process cannot work also...(which mean multiprocess does not work well)

#stream = room.get_stream(error_callback=error)
stream.attach(incoming).start()
raw_input("Waiting for messages (Press ENTER to finish)\n")
stream.stop().join()
#room.leave()
