
Python MIDI + Keyboard Loop Controller
======================================



Overview
--------
This Python script is an experimental audio loop player designed for creative audio manipulation
and live performance experiments.


The script allows you to:

• Play an audio file in an infinite loop
• Control playback using a PC keyboard
• Control playback using a MIDI keyboard
• Modify playback speed in real time
• Control speed using MIDI controllers (0–127 values)
• Reset speed instantly
• Start or stop playback from both keyboard and MIDI

The project is intended for experimentation with sound design, looping, and MIDI interaction.

----------------------------------------------------
Requirements
----------------------------------------------------

Python 3.10 or newer is recommended.

Install required libraries:

pip install pygame pydub keyboard

If you want to use MP3 files you must also install FFmpeg:

https://ffmpeg.org/

----------------------------------------------------
Basic Command
----------------------------------------------------

python improvvisation.py AUDIO_FILE --speed VALUE --keystart KEY --kspeedplus KEY --kspeedminus KEY --kspeeddef KEY

Example:

python improvvisation.py kick.wav --speed 1.0 --keystart 1 --kspeedplus w --kspeedminus q --kspeeddef o

----------------------------------------------------
Parameters
----------------------------------------------------

AUDIO_FILE
Path to the audio file you want to loop.

Supported formats:
WAV
MP3
OGG
FLAC
AAC

WAV is recommended for lowest latency.

--speed
Initial playback speed.

Examples:
1.0 = normal speed
0.5 = half speed
2.0 = double speed

--keystart
Keyboard key used to start or stop the loop.

Allowed values: 1–9

--kspeedplus
Keyboard key used to increase playback speed.

--kspeedminus
Keyboard key used to decrease playback speed.

--kspeeddef
Keyboard key used to reset speed to the original value.

----------------------------------------------------
Keyboard Controls
----------------------------------------------------

Start / Stop Loop
Press the key defined with:

--keystart

Increase Speed
Press the key defined with:

--kspeedplus

Decrease Speed
Press the key defined with:

--kspeedminus

Reset Speed
Press the key defined with:

--kspeeddef

Exit Program
Press:

ESC

----------------------------------------------------
MIDI Support
----------------------------------------------------

The script can also be controlled with a MIDI keyboard.
im using  a M-vave smk25-II but everyone can use 
just to check the channel midi and the key of the keyboard 
connected via usb; use the sketch keyboard IDentify.py for this.

Additional parameters:

--midi-device
ID of the MIDI INPUT device.

--midistart
MIDI note used to start/stop the loop.

--midispeedplus
MIDI note used to increase playback speed.

--midispeedminus
MIDI note used to decrease playback speed.

--midispeeddef
MIDI note used to reset playback speed.

Example:

python improvvisation.py kick.wav --speed 1.0 --keystart 1 --kspeedplus w --kspeedminus q --kspeeddef o --midi-device 17 --midistart 60 --midispeedplus 62 --midispeedminus 59 --midispeeddef 64
 
--------------Complete example of all function---------------------------------------

python improvvisation.py kick1.wav --speed 1.0 --keystart 1 --kspeedplus w --kspeedminus q --kspeeddef o --midi-device 17 --midistart 40 --midispeedplus 62 --midispeedminus 59 --midispeeddef 64 --midispeedctrl 30 --startmode hold

-------------------
#(or --startmode toggle)

###START MODES function###
------------------------------------------------------------

--startmode toggle
Press once to start, press again to stop

--startmode hold
Sound plays only while key or MIDI note is held
-----------------------------

Example MIDI mapping:

60 (C4) -> Start / Stop
62 (D4) -> Speed +
59 (B3) -> Speed -
64 (E4) -> Reset Speed

----------------------------------------------------
MIDI Controller Speed Control
----------------------------------------------------

The script also supports MIDI controllers for continuous speed control.

Controllers send values from 0 to 127.

These values are mapped to a speed range.

Example:

python improvvisation1.py kick.wav --midi-device 17 --midispeedctrl 31

In this case:

Controller 31 controls the playback speed.

Value mapping example:

0   -> speed 0.5
127 -> speed 3.0

You can modify the range:

--midispeedmin
Minimum speed when controller value is 0

--midispeedmax
Maximum speed when controller value is 127

Example:

python improvvisation1.py kick.wav --midi-device 17 --midispeedctrl 31 --midispeedmin 1.0 --midispeedmax 5.0

----------------------------------------------------
How the Script Works
----------------------------------------------------

1. The audio file is loaded using pydub.
2. The playback speed is modified by changing the audio frame rate.
3. The processed audio is exported to a temporary WAV file.
4. pygame plays the audio in an infinite loop.
5. Keyboard and MIDI events control playback and speed changes.

----------------------------------------------------
Typical Use Case
----------------------------------------------------

This script can be used as:

• A live looping experiment tool
• A MIDI controlled sample player
• A real-time sound manipulation experiment
• A creative coding audio project

----------------------------------------------------
Exit
----------------------------------------------------

Press ESC or CTRL+C.

----------------------------------------------------
