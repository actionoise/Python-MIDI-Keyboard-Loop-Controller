import argparse
import os
import threading
import time
import tempfile
import atexit

import keyboard
from pydub import AudioSegment
import pygame
import pygame.midi


# -----------------------------
# Global variables
# -----------------------------
loop_running = False
sound = None
channel = None
assigned_key = None
temp_wav_file = None
lock = threading.Lock()

audio_file_global = None
current_speed = 1.0
initial_speed = 1.0

# Start mode: "toggle" or "hold"
start_mode = "toggle"

# Keyboard state for hold mode
pc_key_is_down = False

# MIDI state for hold mode
midi_start_is_down = False

# Keyboard control keys
key_speed_plus = "w"
key_speed_minus = "q"
key_speed_default = "o"

# MIDI note configuration
midi_device_id = None
midi_input = None
midi_start_note = None
midi_speed_plus_note = None
midi_speed_minus_note = None
midi_speed_default_note = None

# MIDI controller configuration
midi_speed_controller = None
midi_speed_min = 0.5
midi_speed_max = 3.0

# Available speed levels for keyboard and MIDI note step control
speed_levels = [0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0]


# -----------------------------
# Cleanup temporary audio file
# -----------------------------
def cleanup_temp_file():
    global temp_wav_file
    if temp_wav_file and os.path.exists(temp_wav_file):
        try:
            os.remove(temp_wav_file)
        except Exception:
            pass


atexit.register(cleanup_temp_file)


# -----------------------------
# Convert MIDI note number to name
# -----------------------------
def note_name(note_number):
    names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#',
             'G', 'G#', 'A', 'A#', 'B']
    octave = (note_number // 12) - 1
    return f"{names[note_number % 12]}{octave}"


# -----------------------------
# List available MIDI devices
# -----------------------------
def list_midi_devices():
    print("\nAvailable MIDI devices:\n")

    for i in range(pygame.midi.get_count()):
        info = pygame.midi.get_device_info(i)

        interface = info[0].decode(errors="ignore")
        name = info[1].decode(errors="ignore")
        is_input = info[2]
        is_output = info[3]
        opened = info[4]

        io_type = []

        if is_input:
            io_type.append("INPUT")
        if is_output:
            io_type.append("OUTPUT")

        print(f"[{i}] {name} ({interface}) - {'/'.join(io_type)} - opened:{opened}")

    print()


# -----------------------------
# Change audio playback speed
# -----------------------------
def change_speed(audio: AudioSegment, speed: float) -> AudioSegment:
    if speed <= 0:
        raise ValueError("Speed must be greater than 0")

    new_frame_rate = int(audio.frame_rate * speed)

    faster_audio = audio._spawn(
        audio.raw_data,
        overrides={"frame_rate": new_frame_rate}
    )

    return faster_audio.set_frame_rate(audio.frame_rate)


# -----------------------------
# Prepare sound for playback
# -----------------------------
def prepare_sound(audio_file: str, speed: float):
    global sound, temp_wav_file

    cleanup_temp_file()

    audio = AudioSegment.from_file(audio_file)
    processed_audio = change_speed(audio, speed)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    temp_wav_file = tmp.name
    tmp.close()

    processed_audio.export(temp_wav_file, format="wav")
    sound = pygame.mixer.Sound(temp_wav_file)


# -----------------------------
# Start loop
# -----------------------------
def start_loop():
    global loop_running, channel

    with lock:
        if not loop_running:
            channel = sound.play(loops=-1)
            loop_running = True
            print("Loop STARTED")


# -----------------------------
# Stop loop
# -----------------------------
def stop_loop():
    global loop_running, channel

    with lock:
        if channel is not None:
            channel.stop()
        loop_running = False
        print("Loop STOPPED")


# -----------------------------
# Toggle loop
# -----------------------------
def toggle_loop():
    if loop_running:
        stop_loop()
    else:
        start_loop()


# -----------------------------
# Restart loop after speed change
# -----------------------------
def restart_loop_if_running():
    global channel, loop_running

    with lock:
        was_running = loop_running

        if was_running and channel is not None:
            channel.stop()

        if was_running:
            channel = sound.play(loops=-1)


# -----------------------------
# Find nearest speed level index
# -----------------------------
def find_nearest_speed_index(speed):
    closest_index = 0
    min_diff = abs(speed_levels[0] - speed)

    for i, s in enumerate(speed_levels):
        diff = abs(s - speed)
        if diff < min_diff:
            min_diff = diff
            closest_index = i

    return closest_index


# -----------------------------
# Set new playback speed
# -----------------------------
def set_speed(new_speed):
    global current_speed

    current_speed = round(new_speed, 3)

    prepare_sound(audio_file_global, current_speed)
    restart_loop_if_running()

    print(f"Speed set to: {current_speed}")


# -----------------------------
# Increase speed by two levels
# -----------------------------
def increase_speed_two_levels():
    idx = find_nearest_speed_index(current_speed)
    new_idx = min(idx + 2, len(speed_levels) - 1)

    if new_idx != idx:
        set_speed(speed_levels[new_idx])
    else:
        print(f"Speed already at maximum: {current_speed}")


# -----------------------------
# Decrease speed by two levels
# -----------------------------
def decrease_speed_two_levels():
    idx = find_nearest_speed_index(current_speed)
    new_idx = max(idx - 2, 0)

    if new_idx != idx:
        set_speed(speed_levels[new_idx])
    else:
        print(f"Speed already at minimum: {current_speed}")


# -----------------------------
# Reset speed to initial value
# -----------------------------
def reset_speed():
    set_speed(initial_speed)
    print("Speed reset to initial value")


# -----------------------------
# Map MIDI controller value 0-127 to speed range
# -----------------------------
def controller_value_to_speed(value, min_speed, max_speed):
    value = max(0, min(127, value))
    speed = min_speed + (value / 127.0) * (max_speed - min_speed)
    return speed


# -----------------------------
# Handle MIDI note on events
# -----------------------------
def handle_midi_note_on(note):
    global midi_start_is_down

    if midi_start_note is not None and note == midi_start_note:
        print(f"MIDI START: note {note} ({note_name(note)})")

        if start_mode == "toggle":
            toggle_loop()
        else:
            if not midi_start_is_down:
                midi_start_is_down = True
                start_loop()
        return

    if midi_speed_plus_note is not None and note == midi_speed_plus_note:
        print(f"MIDI SPEED + : note {note} ({note_name(note)})")
        increase_speed_two_levels()
        return

    if midi_speed_minus_note is not None and note == midi_speed_minus_note:
        print(f"MIDI SPEED - : note {note} ({note_name(note)})")
        decrease_speed_two_levels()
        return

    if midi_speed_default_note is not None and note == midi_speed_default_note:
        print(f"MIDI SPEED RESET: note {note} ({note_name(note)})")
        reset_speed()
        return


# -----------------------------
# Handle MIDI note off events
# Used in hold mode
# -----------------------------
def handle_midi_note_off(note):
    global midi_start_is_down

    if start_mode == "hold" and midi_start_note is not None and note == midi_start_note:
        if midi_start_is_down:
            midi_start_is_down = False
            print(f"MIDI STOP: note {note} ({note_name(note)})")
            stop_loop()


# -----------------------------
# Handle MIDI control change events
# -----------------------------
def handle_midi_controller(controller, value):
    if midi_speed_controller is not None and controller == midi_speed_controller:
        new_speed = controller_value_to_speed(value, midi_speed_min, midi_speed_max)
        print(f"MIDI CONTROLLER {controller} -> value {value} -> speed {new_speed:.3f}")
        set_speed(new_speed)


# -----------------------------
# Main program
# -----------------------------
def main():
    global assigned_key, audio_file_global, current_speed, initial_speed
    global key_speed_plus, key_speed_minus, key_speed_default
    global midi_device_id, midi_input
    global midi_start_note, midi_speed_plus_note, midi_speed_minus_note, midi_speed_default_note
    global midi_speed_controller, midi_speed_min, midi_speed_max
    global start_mode, pc_key_is_down

    parser = argparse.ArgumentParser(
        description="Audio Loop Player controlled by PC keyboard, MIDI notes and MIDI controllers"
    )

    parser.add_argument("audio_file", help="Path to the audio file")

    parser.add_argument("--speed", type=float, default=1.0, help="Initial loop speed")
    parser.add_argument("--keystart", default="1", help="Keyboard key for start/stop (1-9)")
    parser.add_argument("--kspeedplus", default="w", help="Key to increase speed")
    parser.add_argument("--kspeedminus", default="q", help="Key to decrease speed")
    parser.add_argument("--kspeeddef", default="o", help="Key to reset speed")
    parser.add_argument("--startmode", choices=["toggle", "hold"], default="toggle",
                        help="Start key behavior: toggle or hold")

    parser.add_argument("--midi-device", type=int, default=None, help="MIDI input device ID")
    parser.add_argument("--midistart", type=int, default=None, help="MIDI note for start/stop")
    parser.add_argument("--midispeedplus", type=int, default=None, help="MIDI note for speed increase")
    parser.add_argument("--midispeedminus", type=int, default=None, help="MIDI note for speed decrease")
    parser.add_argument("--midispeeddef", type=int, default=None, help="MIDI note for speed reset")

    parser.add_argument("--midispeedctrl", type=int, default=None,
                        help="MIDI controller number for speed control (example: 30-37)")
    parser.add_argument("--midispeedmin", type=float, default=0.5,
                        help="Minimum speed when MIDI controller value is 0")
    parser.add_argument("--midispeedmax", type=float, default=3.0,
                        help="Maximum speed when MIDI controller value is 127")

    args = parser.parse_args()

    audio_file = args.audio_file
    speed = args.speed
    start_mode = args.startmode

    assigned_key = args.keystart.strip()
    key_speed_plus = args.kspeedplus.strip().lower()
    key_speed_minus = args.kspeedminus.strip().lower()
    key_speed_default = args.kspeeddef.strip().lower()

    midi_device_id = args.midi_device
    midi_start_note = args.midistart
    midi_speed_plus_note = args.midispeedplus
    midi_speed_minus_note = args.midispeedminus
    midi_speed_default_note = args.midispeeddef

    midi_speed_controller = args.midispeedctrl
    midi_speed_min = args.midispeedmin
    midi_speed_max = args.midispeedmax

    if assigned_key not in [str(i) for i in range(1, 10)]:
        raise ValueError("keystart must be a number from 1 to 9")

    if not os.path.isfile(audio_file):
        raise FileNotFoundError(f"File not found: {audio_file}")

    if midi_speed_controller is not None and not (0 <= midi_speed_controller <= 127):
        raise ValueError("midispeedctrl must be between 0 and 127")

    audio_file_global = audio_file
    current_speed = speed
    initial_speed = speed

    pygame.init()
    pygame.mixer.init()
    pygame.midi.init()

    print("Loading audio...")
    prepare_sound(audio_file, speed)

    if midi_device_id is not None:
        list_midi_devices()
        midi_input = pygame.midi.Input(midi_device_id)

    print(f"Audio file: {audio_file}")
    print(f"Initial speed: {speed}")
    print(f"Start mode: {start_mode}")
    print(f"Start key: {assigned_key}")
    print(f"Speed + key: {key_speed_plus}")
    print(f"Speed - key: {key_speed_minus}")
    print(f"Reset speed key: {key_speed_default}")

    if midi_device_id is not None:
        print(f"MIDI device: {midi_device_id}")

        if midi_start_note is not None:
            print(f"MIDI start note: {midi_start_note} ({note_name(midi_start_note)})")
        if midi_speed_plus_note is not None:
            print(f"MIDI speed + note: {midi_speed_plus_note} ({note_name(midi_speed_plus_note)})")
        if midi_speed_minus_note is not None:
            print(f"MIDI speed - note: {midi_speed_minus_note} ({note_name(midi_speed_minus_note)})")
        if midi_speed_default_note is not None:
            print(f"MIDI speed reset note: {midi_speed_default_note} ({note_name(midi_speed_default_note)})")

        if midi_speed_controller is not None:
            print(f"MIDI speed controller: {midi_speed_controller}")
            print(f"Controller speed range: {midi_speed_min} -> {midi_speed_max}")

    print("\nControls:")
    if start_mode == "toggle":
        print(f"Press [{assigned_key}] to start/stop the loop")
    else:
        print(f"Hold [{assigned_key}] to play the loop, release it to stop")
    print(f"Press [{key_speed_plus}] to increase speed")
    print(f"Press [{key_speed_minus}] to decrease speed")
    print(f"Press [{key_speed_default}] to reset speed")
    print("Press [ESC] to exit\n")

    last_plus_time = 0
    last_minus_time = 0
    last_def_time = 0
    last_toggle_time = 0
    debounce_time = 0.25

    try:
        while True:
            now = time.time()

            # PC keyboard start control
            key_pressed = keyboard.is_pressed(assigned_key)

            if start_mode == "toggle":
                if key_pressed and (now - last_toggle_time > debounce_time):
                    toggle_loop()
                    last_toggle_time = now
            else:
                if key_pressed and not pc_key_is_down:
                    pc_key_is_down = True
                    start_loop()
                elif not key_pressed and pc_key_is_down:
                    pc_key_is_down = False
                    stop_loop()

            # PC keyboard speed controls
            if keyboard.is_pressed(key_speed_plus):
                if now - last_plus_time > debounce_time:
                    increase_speed_two_levels()
                    last_plus_time = now

            if keyboard.is_pressed(key_speed_minus):
                if now - last_minus_time > debounce_time:
                    decrease_speed_two_levels()
                    last_minus_time = now

            if keyboard.is_pressed(key_speed_default):
                if now - last_def_time > debounce_time:
                    reset_speed()
                    last_def_time = now

            # MIDI controls
            if midi_input is not None and midi_input.poll():
                events = midi_input.read(20)

                for event in events:
                    data = event[0]

                    status = data[0]
                    data1 = data[1]
                    data2 = data[2]

                    msg_type = status & 0xF0

                    # NOTE ON
                    if msg_type == 0x90 and data2 > 0:
                        handle_midi_note_on(data1)

                    # NOTE OFF or NOTE ON with velocity 0
                    elif msg_type == 0x80 or (msg_type == 0x90 and data2 == 0):
                        handle_midi_note_off(data1)

                    # CONTROL CHANGE
                    elif msg_type == 0xB0:
                        handle_midi_controller(data1, data2)

            if keyboard.is_pressed("esc"):
                break

            time.sleep(0.01)

    except KeyboardInterrupt:
        pass

    finally:
        global loop_running, channel

        loop_running = False

        with lock:
            if channel is not None:
                channel.stop()

        if midi_input is not None:
            midi_input.close()

        pygame.midi.quit()
        pygame.mixer.quit()
        pygame.quit()

        cleanup_temp_file()

        print("Exit...")


if __name__ == "__main__":
    main()