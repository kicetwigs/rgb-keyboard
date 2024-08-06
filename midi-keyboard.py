# Midi keyboard

import time
from keybow2040 import Keybow2040
from keybow_hardware.pim551 import PIM551 as Hardware # for Pico RGB Keypad Base

import usb_midi
import adafruit_midi
from adafruit_midi.note_off import NoteOff
from adafruit_midi.note_on import NoteOn

# Set up Keybow
keybow = Keybow2040(Hardware())
keys = keybow.keys

# Set USB MIDI up on channel 0.
midi = adafruit_midi.MIDI(midi_out=usb_midi.ports[1], out_channel=0)

# The color to set the keys when pressed.
color_std_pressed = (0, 250, 150)
color_std = (0, 20, 10)
color_root_pressed = (250, 0, 150)
color_root = (20, 0, 10)
color_alt = (0, 10, 30)

# Colors to indicate edit mode
rgb_edit_button_color = (0, 0, 0)
rgb_edit_button_color_active = (100, 100, 100)

# Initial values for MIDI note and velocity.
start_note = 48
velocity = 100

rainbow = [
    (23, 0, 0),    #rainbow1 - C
    (25, 10, 0),  #rainbow2 - C#
    (25, 18, 0),  #rainbow3 - D
    (12, 25, 0),  #rainbow4 - D#
    (0, 25, 0),    #rainbow5 - E
    (0, 25, 6),   #rainbow6 - F
    (0, 25, 25),  #rainbow7 - F#
    (0, 6, 25),   #rainbow8 - G
    (0, 0, 23),    #rainbow9 - G#
    (12, 0, 25),  #rainbow10 - A
    (25, 0, 25),  #rainbow11 - A#
    (25, 0, 12)   #rainbow12 - B
]
rainbow_active = [
    (232, 0, 0),    #rainbow1 - C
    (255, 100, 0),  #rainbow2 - C#
    (255, 180, 0),  #rainbow3 - D
    (128, 255, 0),  #rainbow4 - D#
    (0, 255, 0),    #rainbow5 - E
    (0, 255, 62),   #rainbow6 - F
    (0, 255, 255),  #rainbow7 - F#
    (0, 62, 255),   #rainbow8 - G
    (0, 0, 232),    #rainbow9 - G#
    (128, 0, 255),  #rainbow10 - A
    (255, 0, 255),  #rainbow11 - A#
    (255, 0, 128)   #rainbow12 - B
]

# Mode arrays
ionian = [
    21, 23, 24, 99,
    14, 16, 17, 19,
    7, 9, 11, 12,
    0, 2, 4, 5
]
dorian = [
    21, 22, 24, 99,
    14, 15, 17, 19,
    7, 9, 10, 12,
    0, 2, 3, 5
]
phrygian = [
    20, 22, 24, 99,
    13, 15, 17, 19,
    7, 8, 10, 12,
    0, 1, 3, 5
]
lydian = [
    21, 23, 24, 99,
    14, 16, 18, 19,
    7, 9, 11, 12,
    0, 2, 4, 6
]
mixolydian = [
    21, 22, 24, 99,
    14, 16, 17, 19,
    7, 9, 10, 12,
    0, 2, 4, 5
]
aeolian = [
    20, 22, 24, 99,
    14, 15, 17, 19,
    7, 8, 10, 12,
    0, 2, 3, 5
]
locrian = [
    20, 22, 24, 99,
    13, 15, 17, 18,
    6, 8, 10, 12,
    0, 1, 3, 5
]

# List to store modes and colors
modes = [
    ("ionian", ionian, (23, 0, 0)),
    ("dorian", dorian, (25, 18, 0)),
    ("phrygian", phrygian, (0, 25, 0)),
    ("lydian", lydian, (0, 25, 6)),
    ("mixolydian", mixolydian, (0, 6, 25)),
    ("aeolian", aeolian, (12, 0, 25)),
    ("locrian", locrian, (25, 0, 12))
]

current_mode = ionian
current_color = (255, 0, 0)
in_edit_mode = False

def set_mode(mode_index):
    global current_mode, current_color
    if 0 <= mode_index < len(modes):
        _, current_mode, current_color = modes[mode_index]

def set_playing_colors():
    for key in keys:
        if in_edit_mode:
            if key.number == 3:
                key.set_led(*rgb_edit_button_color_active)
            elif 8 <= key.number <= 14:
                index = key.number - 8
                if index < len(modes):
                    _, _, color = modes[index]
                    key.set_led(*color)
                else:
                    key.set_led(0, 0, 0)
            else:
                key.set_led(0, 0, 0)
        else:
            if key.number == 3:
                key.set_led(*rgb_edit_button_color)
            else:
                note_rgb = current_mode[key.number] % 12  # Map to C-B range
                if current_mode[key.number] >= 0:
                    key.set_led(*rainbow[note_rgb])
                else:
                    key.set_led(*color_std)

set_playing_colors()

# Loop through keys and attach decorators.
for key in keys:
    # If pressed, send a MIDI note on command and light key.
    @keybow.on_press(key)
    def press_handler(key):
        global in_edit_mode
        if in_edit_mode:
            # Mode selection logic
            if key.number == 3:
                # Enter edit mode
                in_edit_mode = False
                set_playing_colors()
            elif key.number >= 8:
                set_mode(key.number - 8)
                in_edit_mode = False
                set_playing_colors()
        else:
            if key.number == 3:
                # Enter edit mode
                in_edit_mode = True
                set_playing_colors()
            else:
                note = start_note + current_mode[key.number]
                note_rgb = current_mode[key.number] % 12  # Map to C-B range
                if current_mode[key.number] >= 0:
                    key.set_led(*rainbow_active[note_rgb])
                else:
                    key.set_led(*color_std)
                midi.send(NoteOn(note, velocity))

    # If released, send a MIDI note off command and turn off LED.
    @keybow.on_release(key)
    def release_handler(key):
        global in_edit_mode
        if not in_edit_mode:
            if key.number == 3:
                key.set_led(*rgb_edit_button_color)
            else:
                note = start_note + current_mode[key.number]
                note_rgb = current_mode[key.number] % 12  # Map to C-B range
                if current_mode[key.number] >= 0:
                    key.set_led(*rainbow[note_rgb])
                else:
                    key.set_led(*color_std)
                midi.send(NoteOff(note, 0))

while True:
    # Always remember to call keybow.update()!
    keybow.update()
