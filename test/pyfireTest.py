import pyfire

campfire = pyfire.Campfire("skysourcer", "martin.ku@skysource.com.tw", "abcd1234!", ssl=True)
room = campfire.get_room_by_name("Leader Room")
room.join()
message = raw_input("Enter your message --> ")
if message:
    room.speak(message)
room.leave()