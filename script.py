import webiopi
import json
import time
import datetime
import sys
## Use below for versions of webiopi before 0.7.0
##from webiopi.devices.digital import MCP23017
## Use below for webiopi 0.7.0
from webiopi.devices.digital.mcp23XXX import MCP23017

if sys.version_info.major >= 3:
	import configparser as parser
else:
	import ConfigParser as parser


## Convenient helper for OUT/IN and HIGH/LOW constants
GPIO = webiopi.GPIO

## Channels count
CHANNELS = 16

mcp  = MCP23017()
mcp2 = MCP23017(0x21)

## irrigation settings file path
savePath = "/etc/webiopi/irrigation"

## section where to save in the file, eg. [IRRIGATION]
saveSection = "IRRIGATION"

## Minimum delay between 2 saves
saveDelay = 5 # seconds

## Holds auto/manual mode
auto = False

## Holds start hour/minute
start_h = 0
start_m = 0

## Holds week schedule
days = [False for i in range(7)]

## Hold duration for each channel
durations = [0 for i in range(CHANNELS)]

## Hold manual queue
queue = []

## Hold start time for each channel
started = [0 for i in range(CHANNELS)]

## Hold save state
saveRequired = False 
lastSave = 0

###################################
# app lifecycle functions
# setup/loop/destroy definition

## Setup function, called at WebIOPi startup
def setup():
	global mcp
	## Iterate over all channels
	for i in range(CHANNELS):
		## Set each channel as OUTPUT
		mcp.setFunction (i, GPIO.OUT)
		## Set each channel to LOW
		mcp.digitalWrite(i, GPIO.LOW)
		
	
	## load settings
	loadSettings()
	
## Loop function, running in its own thread
def loop():
	global auto
	if (needWater() and not isRaining()):
		if auto:
			## Check if need to start
			checkStart()
		changeChannel()
	elif (started[0] > 0):
		for i in range(CHANNELS):
			if (started[i] > 0):
				turnOff(i)
			
	## Check if need to save file
	checkSave()
	## Give breath to CPU
	time.sleep(1)

## Destroy function, called at WebIOPi shutdown
def destroy():
	global mcp
	## Iterate over all channels to shut them down
	for i in range(CHANNELS):
		mcp.digitalWrite(i, GPIO.LOW)
	## save config
	saveSettings()


###################################
# Others functions


# Function to read Raining sensor
# returns true if is raining
def isRaining():
	# return mcp2.digitalRead(0) == GPIO.HIGH
	return False

# Function to read humidity sensor
# return true if need water
def needWater():
	# return mcp2.digitalRead(1) == GPIO.LOW
	return True

## Check if start is required
def checkStart():
	global days
	## Get datetime object with current date/time
	now = datetime.datetime.now()
	## Test dayoftheweek, hour and minute
	if (days[now.weekday()] == True) and (now.hour == start_h) and (now.minute == start_m):
		if (started[0] > 0):
			return
		n = iterateChannels(1)
		if (n > 0):
			turnOn(0)
			turnOn(n)

## function to retrieve next channel in auto mode
def iterateChannels(index):
	global started, durations
	## Iterate over channels
	for i in range(index, CHANNELS):
		## Ensure channel need to be started, and not already started
		if (durations[i] > 0) and (started[i] == 0):
				## Actually turn ON channel
				return i
		
	return 0

## function to stop channel and start next channel
def changeChannel():
	global auto, started, durations, queue
	## Get current timestamp in seconds
	timestamp = time.time()
	
	## Iterate over all channels
	for i in range(1, CHANNELS):
		## Test if channel need to be stopped
		if (started[i] > 0) and ((timestamp-started[i]) >= durations[i] * 60):
			## Stop the channel
			turnOff(i)

			## lookup for next channel
			n = 0
			if (auto):
				webiopi.debug("Looking for next channel...")
				n = iterateChannels(i+1)
			elif (len(queue) > 0):
				webiopi.debug("Looking for next channel from manual queue...")
				n = queue.pop(0)

			## turn ON channel found
			if (n > 0):
				turnOn(n)
			## turn OFF master else
			else:
				webiopi.debug("No more channel found")
				turnOff(0)

# function to turn a channel ON
def turnOn(channel):
	global mcp, started
	if (channel == 0):
		webiopi.debug("Turning ON master channel")
	else:
		webiopi.debug("Turning ON channel %d for %d minutes" % (channel, durations[channel]))
	mcp.digitalWrite(channel, GPIO.HIGH)
	## Store start timestamp in seconds
	started[channel] = time.time()

# function to turn a channel OFF
def turnOff(channel):
	global mcp, started
	if (channel == 0):
		webiopi.debug("Turning OFF master channel")
	else:
		webiopi.debug("Turning OFF channel %d" % channel)
	mcp.digitalWrite(channel, GPIO.LOW)
	## Reset start timestamp
	started[channel] = 0

## load settings from file to memory
def loadSettings():
	global auto, start_h, start_m, days, durations
	save = parser.ConfigParser()
	save.optionxform = str
	save.read(savePath)
	if save.has_option(saveSection, "auto"):
		auto = save.getboolean(saveSection, "auto")

	if save.has_option(saveSection, "start-hour"):
		start_h = save.getint(saveSection, "start-hour")

	if save.has_option(saveSection, "start-minute"):
		start_m = save.getint(saveSection, "start-minute")

	for d in range(7):
		if save.has_option(saveSection, "day-%d" % d):
			days[d] = save.getint(saveSection, "day-%d" % d)

	for c in range(CHANNELS):
		if save.has_option(saveSection, "duration-%d" % c):
			durations[c] = save.getint(saveSection, "duration-%d" % c)


## save settings at a fixed maximum rate
## this avoid repeated write on SD card
def checkSave():
	global saveRequired, lastSave
	now = time.time()
	if (saveRequired == True) and ((now-lastSave) > saveDelay):
		saveSettings()
		lastSave = now
		saveRequired = False

## save settings from memory to file
def saveSettings():
	global auto, start_h, start_m, days, durations
	webiopi.debug("Save settings");
	save = parser.ConfigParser()
	save.optionxform = str
	
	save.add_section(saveSection)

	save.set(saveSection, "auto",			"%s" % auto)
	save.set(saveSection, "start-hour", 	"%d" % start_h)
	save.set(saveSection, "start-minute",	"%d" % start_m)

	for d in range(7):
		save.set(saveSection, "day-%d" % d, "%d" % days[d])

	for c in range(CHANNELS):
		save.set(saveSection, "duration-%d" % c, "%d" % durations[c])

	# Writing our configuration file to 'example.cfg'
	with open(savePath, 'w') as savefile:
		save.write(savefile)		

## function to return formated start time
def getStart():
	## Format is "00:00" / 24h mode
	return "%02d:%02d" % (start_h, start_m)


## function to return mode as string
def getMode():
	global auto
	if (auto):
		return "auto"
	return "manual"

#########################
# Macro definition part #

## Macro taking two arguments to set start time
## - hour:   start hour
## - minute: start minute
## returns effective new start time
@webiopi.macro
def setStart(hour, minute):
	global start_h, start_m, saveRequired
	## Cast and store value in memory
	start_h = int(hour)
	start_m = int(minute)

	saveRequired = True;

	return getStart()

def getDay(day):
	return "%d" % days[int(day)]

## Macro taking two arguments to schedule the given day
@webiopi.macro
def setDay(day, value):
	global days, saveRequired
	## Cast and store value in memory
	days[int(day)] = bool(int(value))

	saveRequired = True;

	return getDay(day)

## Macro taking two argument to set duration for the given channel
@webiopi.macro
def setDuration(channel, duration):
	global saveRequired
	## Cast and store value in memory
	durations[int(channel)] = int(duration)

	saveRequired = True;

	return "%d" % durations[int(channel)]


## Macro taking one argument to set mode
## mode can be either "auto" or "manual"
@webiopi.macro
def setMode(mode):
	global auto, queue, saveRequired

	if (mode == "auto"):
		auto = True
		# reset manual queue
		queue = []

	elif (mode == "manual"):
		auto = False

	# Turn off started channels
	for c in range(CHANNELS):
		if (started[c] > 0):
			turnOff(c)

	saveRequired = True;

	return getMode()

## macro to switch master channel on/off
@webiopi.macro
def switchMaster(value):
	global auto, queue
	value = int(value)
	
	# ignore if auto mode enabled
	if (auto):
		# return current state
		return "%d" % started[0] > 0

	# turning on master
	if (value == 1):
		# fill queue if empty
		if (len(queue) == 0):
			for i in range(1, CHANNELS):
				if (durations[i] > 0):
					queue.append(i)
		
		# take first queue element
		c = queue.pop(0)
		# turn on master channel and first channel from queue
		turnOn(0)
		turnOn(c)

	# turning off master
	else:
		# reset queue
		queue = []
		# turn off started channels
		for i in range(CHANNELS):
			if (started[i] > 0):
				turnOff(i)
	# return value set
	return "%d" % value

## macro to switch a single channel
@webiopi.macro
def switchChannel(channel, value):
	global auto, started, queue, durations
	
	# ignore master channel
	if (channel == 0):
		return "%d" % started[0] > 0

	channel = int(channel)
	value   = int(value)

	# ignore if mode is auto
	if auto:
		# return 0 if no duration set
		if (durations[channel] == 0):
			return "0"
		
		# return 1 if channel is started
		if (started[channel] > 0):
			return "1"

		# we need to check if channel is waiting
		for i in range(1, CHANNELS):
			# find and compare to started channel 
			if started[i] > 0 and i < channel:
				# return -1 (wait) if channel is after started channel
				if durations[channel] > 0:
					return "-1"
		return "0"

	# manual mode
	# turning on channel
	if (value == 1):
		# master channel not started
		if (started[0] == 0):
			# turning master and desired channels
			turnOn(0)
			turnOn(channel)
			return "1"
		
		# master is alredy started
		for i in range(len(queue)):
			# return if channel already in queue
			if queue[i] == channel:
				return "-1"
		# append channel to queue
		queue.append(channel)
		return "-1"

	# manual mode
	# turning off channel

	# remove from queue if exists
	for i in range(len(queue)):
		if queue[i] == channel:
			queue.pop(i)
			break
	
	# turn off channel if started
	if (started[channel] > 0):
		turnOff(channel)
		# have more channels
		if len(queue) > 0:
			# get next channel
			n = queue.pop(0)
			# turn on next channel
			turnOn(n)
		# no more channel
		else:
			# turn off master channel
			turnOff(0)

	return "0"

## Macro to return the whole application state in JSON
@webiopi.macro
def getAll():
	global days, durations, started, queue
	response = {}
	response["mode"] = getMode()
	response["start"] = getStart()
	response["days"] = days
	response["durations"] = durations
	channels = [int(started[i] > 0) for i in range(CHANNELS)]
	
		
	# started manually, set waiting channels from queue
	if started[0] > 0 and not auto:
		for c in queue:
			channels[c] = -1

	# else iterate over channels
	else:
		i=1
		# until finding started channel
		while (i < CHANNELS) and (started[i] == 0):
			i+=1
		# following channels are waiting
		i+=1
		while (i < CHANNELS):
			if durations[i] > 0:
				channels[i] = -1
			i+=1

	response["channels"] = channels

	# return a JSON formated result
	return json.dumps(response)
