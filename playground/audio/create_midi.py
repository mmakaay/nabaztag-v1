#!/usr/bin/env python3

from midiutil import *

MyMIDI = MIDIFile(1, file_format=0)
track = 0
channel = 0
pitch = 60
time = 0
duration = 1
volume = 150
MyMIDI.addProgramChange(track,channel,0,19)
MyMIDI.addNote(track,channel,60,0,duration,volume)
MyMIDI.addNote(track,channel,80,0,duration,volume)
MyMIDI.addNote(track,channel,93,1,duration,volume)

with open('my.mid', 'wb') as f:
    MyMIDI.writeFile(f)
