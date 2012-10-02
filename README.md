# Skyfire: Use skype as your campfire client app

This package is inspired by the work on [Turn Skype into your own Campfire desktop client].
The goal of this package is to wrap skype so that you can interact with campfire through it.

## IDEA ##

We bind **Skype Chat Groups** with **Campfire Rooms**. 
Bot would transfer the messages for you. 
In fact, you can use Skyfire without Campfire to make Skype has the concept of **Chat Room**.

## LICENSE ##

Skyfire is released under the [GPL 2.0 license].

## INSTALLATION ##

### REQUIRED LIBRARY ###

#### Pyfire ####

https://github.com/mariano/pyfire

#### Skype4Py ####

http://sourceforge.net/projects/skype4py/
**Note:** Need to add a argument **use_process** to get_stream function and its return under Room class

#### PyAIML ####

http://pyaiml.sourceforge.net/

### OTHER ###

#### Skype Settings ####

You'll need a Skype user to act as campfire bot. Register a new skype account is a recommended way.
Here's the things you should do before run the service:
* Login bot on Skype
* Create chat groups. The topics of chat groups and rooms' names should be exactly the same. (This is our way to bind rooms with Skype, so we CANNOT handle any room related change (e.g., room name changed, add or delete room) so far).
* Find uri of chat groups and write down the mappings in config.
* Change status of bot to INVISIBLE
* Be friends with people who want to use this service

#### Configuration ####

Change example.cfg according to your situations.

## Usage ##

    $ python skyfire.py

## Other Resource ##

* Skype chat command: https://support.skype.com/en-us/faq/fa10042/what-are-chat-commands-and-roles
* Skype API Reference: http://developer.skype.com/public-api-reference

[Turn Skype into your own Campfire desktop client]: http://chozhiyath.wordpress.com/2010/11/22/campfire-client/
[GPL 2.0 license]: http://www.gnu.org/licenses/gpl-2.0.txt
