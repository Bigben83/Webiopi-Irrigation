# Webiopi-Irrigation
This is an irrigation program written for webiopi

Irrigation System WebIOPi-based application. It can work with PiFace, IO PI, or any I/O expander supported by WebIOPi.
The system provides both manual and automatic mode, with a week schedule to activate each station in sequence for a given duration.

On automatic mode, channels start in sequence at the start time. It includes a master solenoid valve setting that can turn off the mains water
to safe guard against hose bursts etc.
When clicking on master channel in manual mode, all channels with a duration set will start in sequence.
You can also click on each channel to select several of them and start irrigation immediately.

You will found isRaining and needWater Python functions. It respectively return False and True for the moment.  This is for rain sensing etc.

