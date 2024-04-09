# ableton-osc-twitch
Twitch IRC bot to control Ableton Live via AbletonOSC

# WARNING:
Currently Mac-only (PC version in the works)

# Setup
1. Install [AbletonOSC](https://github.com/ideoforms/AbletonOSC) 
2. Run the script, providing arguments for Twitch username, ip of AbletonOSC, and port of AbletonOSC:
```python3 ableton-osc-twitch.py -u username -i 127.0.0.1 -p 11000```
3. Let your chat go wild using the !ableton command:
```!ableton <args>```

## Available args
```
play
play clip
play clip <track> <clip>
stop
stop clip
stop clip <track> <clip>
create track midi
create track audio
create clip <track> <clip> <len_beats>
create scene
create note <name/num> <vel> <dur> <start>
search <device name>
select track <track>
select clip <track> <clip>
save
tempo <tempo>
```

# Platform Support
Currently this only works on MacOS due to using a few keypress combinations to do things like search for and insert devices onto tracks or save the session.  I might get around to making it multi-platform, but if you figure it out first, feel free to raise a PR!