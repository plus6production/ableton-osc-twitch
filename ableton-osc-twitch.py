from twitch_chat_irc import twitch_chat_irc
from pythonosc import udp_client
import applescript
import argparse

#example message
'''
{'badge-info': 'subscriber/21', 'badges': 'broadcaster/1,subscriber/3012,premium/1', 'client-nonce': '5f4f5ee4ee5144a229daf2bfb65944c2', 'color': '#FF69B4', 'display-name': 'plus6production', 'emotes': '', 'first-msg': '0', 'flags': '', 'id': 'b8053790-b0f7-48b7-a820-4ee8933ffaeb', 'mod': '0', 'returning-chatter': '0', 'room-id': '708942893', 'subscriber': '1', 'tmi-sent-ts': '1712615382323', 'turbo': '0', 'user-id': '708942893', 'user-type': '', 'message': 'still testing'}
'''

NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
OCTAVES = list(range(11))
NOTES_IN_OCTAVE = len(NOTES)
OCTAVE_OFFSET = 2

def note_to_number(note: str) -> int:

    note_name = ''
    octave = 0

    if len(note) == 4: # Has both accidental and negative
        note_name = note[:2]
        octave = int(note[2:])
    elif len(note) == 3:
        if note[1] == '-': # Low octave, no accidental
            note_name = note[0:1]
            octave = int(note[1:])
        else: # Accidental
            note_name = note[0:2]
            octave = int(note[2:])
    elif len(note) == 2:
        note_name = note[0:1]
        octave = int(note[1:])
    else:
        raise Exception(f'Invalid note name {note}.')

    octave += OCTAVE_OFFSET
    note_num = 60
    if note_name in NOTES and octave in OCTAVES:
        note_num = NOTES.index(note_name)
        note_num += (NOTES_IN_OCTAVE * octave)
    else:
        raise Exception(f'Invalid note name {note_name}.')

    if note_num < 0:
        note_num = 0
    if note_num > 127:
        note_num = 127

    return note_num

# CAN THROW
def human_readable_index_to_internal(i):
    return int(i) - 1

class TwitchAbletonOsc:

    def __init__(self, ip, port):
        self.client = udp_client.SimpleUDPClient(ip, port)
        self.current_track = 0
        self.current_clip = 0
        self.current_scene = 0

        ### Offset into clip in beats, used for note add
        self.current_start_time = 0

    def parse_select_subcommand(self, args):
        if args[0] == 'clip':
            # need track and scene index
            if len(args) >= 3 and args[1].isdigit() and args[2].isdigit():
                print(f'select clip on track {args[1]} scene {args[2]}')
                self.current_track = human_readable_index_to_internal(args[1])
                self.current_clip = human_readable_index_to_internal(args[2])
                self.client.send_message('/live/view/set/selected_clip', [self.current_track, self.current_clip])
        elif args[0] == 'track':
            # need track index
            if len(args) >= 2 and args[1].isdigit():
                self.current_track = human_readable_index_to_internal(args[1])
                self.client.send_message('/live/view/set/selected_track', self.current_track)
        elif args[0] == 'scene':
            # need scene index
            if len(args) >= 2 and args[1].isdigit():
                self.current_scene = human_readable_index_to_internal(args[1])
                self.client.send_message('/live/view/set/selected_scene', self.current_scene)

    def parse_delete_subcommand(self, args):
        pass

    def parse_note_name_to_midi_num(self, name):
        # TODO
        pass

    def parse_note_subcommand(self, args, isCreate):
        # Osc takes track, clip, then array of notes
        # Just use currently selected
        # Chat user will just enter pitch, velocity, duration (optional), start (optional)

        if len(args) < 1:
            return

        if args[0].isdigit():
            note_num = int(args[0])
        else:
            try:
                note_num = note_to_number(args[0])
            except Exception as e:
                print(e)
                return

        if len(args) > 1 and args[1].isdigit():
            velocity = int(args[1])
        else:
            velocity = 100

        duration = 1.0
        if len(args) > 2:
            try:
                duration = float(args[2])
            except:
                raise Exception(f'{args[2]} did not parse to float')

        start = self.current_start_time
        if len(args) > 3:
            try:
                start = float(args[3])
                self.current_start_time = start
            except:
                raise Exception(f'{args[2]} did not parse to float')
        
        self.client.send_message('/live/clip/add/notes', [self.current_track, self.current_clip, note_num, start, duration, velocity, False])
        self.current_start_time += duration

    def parse_create_subcommand(self, args):
        if args[0] == 'clip':
            # Needs track, clip, and length
            if len(args) >= 4 and args[1].isdigit() and args[2].isdigit() and args[3].isdigit():
                print(f'create clip of length {args[3]} on track {args[1]} slot {args[2]}')
                self.current_track = human_readable_index_to_internal(args[1])
                self.current_clip = human_readable_index_to_internal(args[2])
                self.client.send_message('/live/clip_slot/create_clip', [self.current_track, self.current_clip, int(args[3])])
        elif args[0] == 'track':
            if len(args) >= 2:
                if args[1] == 'midi':
                    self.client.send_message('/live/song/create_midi_track', -1)
                elif args[1] == 'audio':
                    self.client.send_message('/live/song/create_audio_track', -1)
            else:
                # default to MIDI
                self.client.send_message('/live/song/create_midi_track', -1)
        elif args[0] == 'scene':
            self.client.send_message('/live/song/create_scene', -1)
        elif args[0] == 'note':
            self.parse_note_subcommand(args[1:], True)

    def parse_search_subcommand(self, args):
        search_string = ' '.join(map(str, args))
        script = applescript.AppleScript(f'''
            tell application id (id of application "Live")
                activate
            end tell                             
            tell application "System Events"
              delay 0.5
              keystroke "f" using command down
              delay 0.5
              keystroke "{search_string}"
              delay 0.5
              keystroke return
              delay 0.2
              keystroke return
            end tell
        ''')
        print(script.run())

    def handle_save_command(self):
        script = applescript.AppleScript(f'''
            tell application id (id of application "Live")
                activate
            end tell                             
            tell application "System Events"
              delay 0.5
              keystroke "s" using command down
              delay 0.5
            end tell
        ''')
        print(script.run())

    def parse_tempo_command(self, args):
        if len(args) < 1:
            return
        
        tempo = 120.0
        try:
            tempo = float(args[0])
            self.client.send_message('/live/song/set/tempo', [tempo])
        except Exception as e:
            print(f'Invalid tempo string {args[0]}')
        
        return

    def parse_ableton_command(self, args):
        if args[0] == 'play':
            if len(args) > 1 and args[1] == 'clip':
                # Fire clip
                if len(args) > 3 and args[2].isdigit() and args[3].isdigit():
                    self.client.send_message('/live/clip/fire', [human_readable_index_to_internal(args[2]), human_readable_index_to_internal(args[3])])
                else:
                    self.client.send_message('/live/clip/fire', [self.current_track, self.current_clip])
            elif len(args) == 1:
                # Normal play
                self.client.send_message('/live/song/start_playing', None)
        elif args[0] == 'stop':
            if len(args) > 1 and args[1] == 'clip':
                # Stop clip
                if len(args) > 3 and args[2].isdigit() and args[3].isdigit():
                    self.client.send_message('/live/clip/stop', [human_readable_index_to_internal(args[2]), human_readable_index_to_internal(args[3])])
                else:
                    self.client.send_message('/live/clip/stop', [self.current_track, self.current_clip])
            elif len(args) == 1:
                # Normal stop
                self.client.send_message('/live/song/stop_playing', None)
        elif args[0] == 'create':
            self.parse_create_subcommand(args[1:])
        elif args[0] == 'delete':
            self.parse_delete_subcommand(args[1:])
        elif args[0] == 'select':
            self.parse_select_subcommand(args[1:])
        elif args[0] == 'search':
            self.parse_search_subcommand(args[1:])
        elif args[0] == 'save':
            self.handle_save_command()
        elif args[0] == 'tempo':
            self.parse_tempo_command(args[1:])

ableton_osc = None

def handle_chat_message(message):
    message_body = message['message']
    message_split = message_body.split(' ')
    if len(message_split) != 0 and message_body[0] == '!':
        #print(message_split[0])
        command = message_split[0][1:]
        params = message_split[1:]
        if command == 'ableton' and len(params) > 0:
            print("We got here", params)
            ableton_osc.parse_ableton_command(params)
        elif command == 'ott':
            ableton_osc.parse_ableton_command(['search', 'OTT.adv'])

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--user', help='Twitch Username')
    parser.add_argument('-i', '--ip', help="IP address of AbletonOSC")
    parser.add_argument('-p', '--port', help="Port of AbletonOSC", type=int)

    args = parser.parse_args()

    ableton_osc = TwitchAbletonOsc(args.ip, args.port)
    connection = twitch_chat_irc.TwitchChatIRC()
    connection.listen(args.user, on_message=handle_chat_message)