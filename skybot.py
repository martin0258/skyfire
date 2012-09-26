# -*- coding: utf-8 -*-
import os, aiml
os.chdir(os.path.dirname(os.path.abspath(__file__)))
bot = aiml.Kernel()
bot.learn('skysource.aiml')
defaultResponse = "Hard to guess what do you mean...\nCan you say more?"
def GetResponse(speech):
  response = bot.respond(speech) 
  return response if len(response)>0 and response.find("WARNING")==-1 else defaultResponse
if __name__ == "__main__":
  speech = ''
  while speech != 'quit':
    speech = raw_input('>')
    print GetResponse(speech).decode('utf-8')
