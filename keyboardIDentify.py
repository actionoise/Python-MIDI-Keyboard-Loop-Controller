import pygame
import pygame.midi

def list_midi_devices():
    print("Dispositivi MIDI disponibili:\n")
    for i in range(pygame.midi.get_count()):
        info = pygame.midi.get_device_info(i)
        interface = info[0].decode()
        name = info[1].decode()
        is_input = info[2]
        is_output = info[3]
        opened = info[4]

        io_type = []
        if is_input:
            io_type.append("INPUT")
        if is_output:
            io_type.append("OUTPUT")

        print(f"[{i}] {name} ({interface}) - {'/'.join(io_type)} - aperto:{opened}")

def note_name(note_number):
    names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    octave = (note_number // 12) - 1
    name = names[note_number % 12]
    return f"{name}{octave}"

def main():
    pygame.init()
    pygame.midi.init()

    try:
        list_midi_devices()
        print()

        device_id = int(input("Inserisci l'ID del dispositivo MIDI INPUT da usare: "))
        midi_input = pygame.midi.Input(device_id)

        print("\nAscolto eventi MIDI...")
        print("Premi i tasti della tastiera MIDI per identificarli.")
        print("Premi CTRL+C per uscire.\n")

        while True:
            if midi_input.poll():
                events = midi_input.read(20)

                for event in events:
                    data = event[0]
                    timestamp = event[1]

                    status = data[0]
                    data1 = data[1]
                    data2 = data[2]

                    msg_type = status & 0xF0
                    channel = (status & 0x0F) + 1

                    if msg_type == 0x90:
                        if data2 > 0:
                            print(
                                f"NOTE ON   | Canale:{channel} | Nota:{data1} ({note_name(data1)}) | Velocity:{data2} | Time:{timestamp}"
                            )
                        else:
                            print(
                                f"NOTE OFF  | Canale:{channel} | Nota:{data1} ({note_name(data1)}) | Velocity:0 | Time:{timestamp}"
                            )

                    elif msg_type == 0x80:
                        print(
                            f"NOTE OFF  | Canale:{channel} | Nota:{data1} ({note_name(data1)}) | Velocity:{data2} | Time:{timestamp}"
                        )

                    elif msg_type == 0xB0:
                        print(
                            f"CONTROL CHANGE | Canale:{channel} | Controller:{data1} | Valore:{data2} | Time:{timestamp}"
                        )

                    elif msg_type == 0xE0:
                        value = data1 + (data2 << 7)
                        print(
                            f"PITCH BEND | Canale:{channel} | Valore:{value} | Time:{timestamp}"
                        )

                    else:
                        print(
                            f"ALTRO EVENTO | Status:{status} | Data1:{data1} | Data2:{data2} | Canale:{channel} | Time:{timestamp}"
                        )

    except KeyboardInterrupt:
        print("\nUscita...")
    except Exception as e:
        print(f"Errore: {e}")
    finally:
        try:
            midi_input.close()
        except:
            pass
        pygame.midi.quit()
        pygame.quit()

if __name__ == "__main__":
    main()