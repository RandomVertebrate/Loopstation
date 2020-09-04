print('LOADING...')

import pyaudio
import numpy as np
import wave

settings_file = open('Config/settings.prt', 'r')
parameters = settings_file.readlines()
settings_file.close()

RATE = int(parameters[0]) #sample rate                                                               SETTING 1
CHUNK = int(parameters[1]) #buffer size                                                              SETTING 2
FORMAT = pyaudio.paInt16 #16-bit audio
CHANNELS = 1 #mono

latency_in_milliseconds = int(parameters[2])                                                        #SETTING 3
latency_in_buffers = int((RATE / CHUNK) * (latency_in_milliseconds / 1000))
latency_in_samples = latency_in_buffers * CHUNK

metronome_beeplength = int(parameters[3]) #length of metronome beep in buffers                      #SETTING 4

tempo = int(parameters[4])                                                                          #SETTING 5
beats_per_bar = int(parameters[5])                                                                  #SETTING 6
bars_in_loop1 = int(parameters[6])                                                                  #SETTING 7
bars_of_countin = int(parameters[7])                                                                #SETTING 8

relative_length_loop = (1, int(parameters[8]), int(parameters[9]), int(parameters[10]))             #SETTINGS 9, 10, 11 (element 0 always has value 1)
#relative_length_loop contains lengths of loops relative to loop 1. Allowed 1, 2, 3, 4.

buffers_per_beat = int((RATE / CHUNK) * (60 / tempo))

SESSION_RECORD = bool(int(parameters[11]))                                                          #SETTING 12

live_track_recording = False

if SESSION_RECORD: #open and setup files
    rec1 = wave.open('Session/track1.wav', 'wb')
    rec2 = wave.open('Session/track2.wav', 'wb')
    rec3 = wave.open('Session/track3.wav', 'wb')
    rec4 = wave.open('Session/track4.wav', 'wb')
    recL = wave.open('Session/solo.wav', 'wb')
    rec1.setnchannels(1); rec1.setsampwidth(2); rec1.setframerate(RATE);
    rec2.setnchannels(1); rec2.setsampwidth(2); rec2.setframerate(RATE);
    rec3.setnchannels(1); rec3.setsampwidth(2); rec3.setframerate(RATE);
    rec4.setnchannels(1); rec4.setsampwidth(2); rec4.setframerate(RATE);
    recL.setnchannels(1); recL.setsampwidth(2); recL.setframerate(RATE);

silence = np.zeros(CHUNK, dtype = np.int16) #buffer containing silence

click = np.zeros(CHUNK, dtype = np.int16)
for i in range(CHUNK):
    click[i] = 1000 * ((i % 20) / 20 - 0.5)
#buffer click now contains a sawtooth wave. RHS of modulo controls frequency.

loop1_plays = 0 #keeps track of how many times loop 1 has played through.

class audioloop:

    def __init__(self, relative_length):
        self.buffer_count = int(relative_length * (RATE / CHUNK) * (60 / tempo) * beats_per_bar * bars_in_loop1)
        self.audio = np.zeros([self.buffer_count, CHUNK], dtype = np.int16)
        self.tmpbuf = np.zeros([CHUNK], dtype = np.int16)
        self.readp = 0
        self.writep = self.buffer_count - 1 - latency_in_buffers
        self.mix_ratio = 1.0
        self.isrecording = False
        self.isplaying = True

    def incptrs(self): #now one funtion to increment both read and write pointers
        self.writep = ((self.writep + 1) % self.buffer_count)
        self.readp = ((self.readp + 1) % self.buffer_count)
        
    def is_restarting(self):
        if (self.readp == 0):
            return True
        else:
            return False

    def restart(self):
        self.readp = 0
        self.writep = self.buffer_count - latency_in_buffers

    def toggle_recording(self):
        if self.isrecording:
            self.isrecording = False
        else:
            self.isrecording = True

    def toggle_playing(self):
        if self.isplaying:
            self.isplaying = False
        else:
            self.isplaying = True

    def read(self):
        tmp = self.readp
        self.incptrs()
        return(self.audio[tmp, :])

    def dub(self, data):
        datadump = np.frombuffer(data, dtype = np.int16)
        for i in range(CHUNK):
            self.audio[self.writep, i] = self.audio[self.writep, i] * 0.9 + datadump[i] * self.mix_ratio

loop1 = audioloop(relative_length_loop[0])
loop2 = audioloop(relative_length_loop[1])
loop3 = audioloop(relative_length_loop[2])
loop4 = audioloop(relative_length_loop[3])

def restart_loops(length):                                               #restart all loops of a particular relative length
    if (length == relative_length_loop[1]):
        loop2.restart()
    if (length == relative_length_loop[2]):
        loop3.restart()
    if (length == relative_length_loop[3]):
        loop4.restart()

pa = pyaudio.PyAudio()

def live_callback(in_data, frame_count, time_info, status):              #records microphone input straight to file
    if live_track_recording:
        recL.writeframesraw(np.frombuffer(in_data, dtype = np.int16))    #incoming data converted to integer array and written to file
    else:
        recL.writeframesraw(silence)
    return (silence, pyaudio.paContinue)

def loop1_callback(in_data, frame_count, time_info, status):
    global loop1
    global loop1_plays

    if loop1.isrecording:
        loop1.dub(in_data)
        if SESSION_RECORD:
            rec1.writeframesraw(np.frombuffer(in_data, dtype = np.int16)) #convert and write incoming buffer to file.
        
    if loop1.is_restarting():
        loop1_plays = loop1_plays + 1
        if loop1.isrecording:
            loop1.mix_ratio = loop1.mix_ratio * 0.9                       #nth overdub mixed in 0.9**n :0.9 ratio. Keeps all overdubs equal.
            
        #making sure loops don't drift out of sync:           
        restart_loops(1)                                                  #restart any other loops of same length as loop1
        if (loop1_plays % 2 == 0):                                        #every two complete loops of loop 1,
            restart_loops(2)                                              #restart loops double the length of loop1
            if (loop1_plays % 4 == 0):
                restart_loops(4)                                          #4 times the length
        elif (loop1_plays % 3 == 0):
            restart_loops(3)                                              #3 times the length
    
    if loop1.isplaying:
        loop1.tmpbuf = loop1.read()                                       #temporary buffer stores data to be played
        if not loop1.isrecording:                                         #(loop.isrecording) case for session recording already taken care of earlier
            if SESSION_RECORD:
                rec1.writeframesraw(loop1.tmpbuf)                         #data being played is first written to file
        return (loop1.tmpbuf, pyaudio.paContinue)                         #returning a buffer from the stream callback function plays it
    else:
        loop1.incptrs()                                                   #not needed when audioloop.read() is being called
        if not loop1.isrecording:
            if SESSION_RECORD:
                rec1.writeframesraw(silence)                              #since not playing and not recording, write silence to file
        return (silence, pyaudio.paContinue)                              #since not playing, play silence


#other three callback functions are very similar, minus the restart() stuff:

def loop2_callback(in_data, frame_count, time_info, status):
    global loop2

    if loop2.isrecording:
        loop2.dub(in_data)
        if SESSION_RECORD:
            rec2.writeframesraw(np.frombuffer(in_data, dtype = np.int16))
        if loop2.is_restarting():
            loop2.mix_ratio = loop2.mix_ratio * 0.9
    
    if loop2.isplaying:
        loop2.tmpbuf = loop2.read()
        if not loop2.isrecording:
            if SESSION_RECORD:
                rec2.writeframesraw(loop2.tmpbuf)
        return (loop2.tmpbuf, pyaudio.paContinue)
    else:
        loop2.incptrs()
        if not loop2.isrecording:
            if SESSION_RECORD:
                rec2.writeframesraw(silence)
        return (silence, pyaudio.paContinue)

def loop3_callback(in_data, frame_count, time_info, status):
    global loop3

    if loop3.isrecording:
        loop3.dub(in_data)
        if SESSION_RECORD:
            rec3.writeframesraw(np.frombuffer(in_data, dtype = np.int16))
        if loop3.is_restarting():
            loop3.mix_ratio = loop3.mix_ratio * 0.9
    
    if loop3.isplaying:
        loop3.tmpbuf = loop3.read()
        if not loop3.isrecording:
            if SESSION_RECORD:
                rec3.writeframesraw(loop3.tmpbuf)
        return (loop3.tmpbuf, pyaudio.paContinue)
    else:
        loop3.incptrs()
        if not loop3.isrecording:
            if SESSION_RECORD:
                rec3.writeframesraw(silence)
        return (silence, pyaudio.paContinue)

def loop4_callback(in_data, frame_count, time_info, status):
    global loop4

    if loop4.isrecording:
        loop4.dub(in_data)
        if SESSION_RECORD:
            rec4.writeframesraw(np.frombuffer(in_data, dtype = np.int16))
        if loop4.is_restarting():
            loop4.mix_ratio = loop4.mix_ratio * 0.9
    
    if loop4.isplaying:
        loop4.tmpbuf = loop4.read()
        if not loop4.isrecording:
            if SESSION_RECORD:
                rec4.writeframesraw(loop4.tmpbuf)
        return (loop4.tmpbuf, pyaudio.paContinue)
    else:
        loop4.incptrs()
        if not loop4.isrecording:
            if SESSION_RECORD:
                rec4.writeframesraw(silence)
        return (silence, pyaudio.paContinue)

metronome_stream = pa.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=False,
    output=True,
    frames_per_buffer = CHUNK,
    start = False
    #no callback function, this stream is opened in blocking mode.
)

loop1_stream = pa.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    output=True,
    frames_per_buffer = CHUNK,
    start = False,
    stream_callback = loop1_callback
)

loop2_stream = pa.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    output=True,
    frames_per_buffer = CHUNK,
    start = False,
    stream_callback = loop2_callback
)

loop3_stream = pa.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    output=True,
    frames_per_buffer = CHUNK,
    start = False,
    stream_callback = loop3_callback
)

loop4_stream = pa.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    output=True,
    frames_per_buffer = CHUNK,
    start = False,
    stream_callback = loop4_callback
)

live_stream = pa.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    output=False,
    frames_per_buffer = CHUNK,
    start = False,
    stream_callback = live_callback
)

#count-in:

print('COUNT-IN...')
buffers_of_countin = buffers_per_beat * beats_per_bar * bars_of_countin

metronome_stream.start_stream()

for i in range(buffers_of_countin): #count-in
    if (i % buffers_per_beat < metronome_beeplength):
        metronome_stream.write(click, CHUNK)
    else:
        metronome_stream.write(silence, CHUNK)


#starting recording:

loop1.isrecording = True

loop1_stream.start_stream()
loop2_stream.start_stream()
loop3_stream.start_stream()
loop4_stream.start_stream()

if SESSION_RECORD:
    live_stream.start_stream()

#metronome:

print('TRACK 1 RECORDING')

for i in range(loop1.buffer_count):
    if (i % buffers_per_beat < metronome_beeplength):
        metronome_stream.write(click, CHUNK)
    else:
        metronome_stream.write(silence, CHUNK)

metronome_stream.stop_stream()

print('Tracks:   1    2   3    4')

#what follows is temporary implementation of:
#realtime toggling of isrecording and isplaying variables for all loops.
#entering q w e r mutes or unmutes each track. entering a s d f starts or stops recording.
#entering x exits.

#constraint: isrecording cannot be True for any two loops at once (Bad audio results).
#constraint: live_track_recording cannot be True if isrecording is true for any loop.

def printstatus():
    print('Playback: ' + str(loop1.isplaying) + str(loop2.isplaying) + str(loop3.isplaying) + str(loop4.isplaying))
    print('Recording: ' + str(loop1.isrecording) + str(loop2.isrecording) + str(loop3.isrecording) + str(loop4.isrecording))

ans = '\0'

while True:
    if (loop1.isrecording or loop2.isrecording or loop3.isrecording or loop4.isrecording): #two streams seemingly cannot record from the
        live_track_recording = False                                                       #microphone simultaneously. "Live" stream records and
    else:                                                                                  #writes to file when no other streams record.
        live_track_recording = True
    printstatus()
    ans = input()
    if (ans == 'a'):
        loop1.toggle_recording()
        loop2.isrecording = False                                                          #making sure multiple streams are never
        loop3.isrecording = False                                                          #recording simultaneously.
        loop4.isrecording = False
    elif (ans == 's'):
        loop2.toggle_recording()
        loop3.isrecording = False
        loop4.isrecording = False
        loop1.isrecording = False
    elif (ans == 'd'):
        loop3.toggle_recording()
        loop2.isrecording = False
        loop1.isrecording = False
        loop4.isrecording = False
    elif (ans == 'f'):
        loop4.toggle_recording()
        loop2.isrecording = False
        loop3.isrecording = False
        loop1.isrecording = False
    elif (ans == 'q'):
        loop1.toggle_playing()
    elif (ans == 'w'):
        loop2.toggle_playing()
    elif (ans == 'e'):
        loop3.toggle_playing()
    elif (ans == 'r'):
        loop4.toggle_playing()
    elif (ans == 'x'):
        break
#ending here: temporary implementation of realtime toggling of isrecording and isplaying variables for all loops.

loop1_stream.close()
loop2_stream.close()
loop3_stream.close()
loop4_stream.close()

if SESSION_RECORD:
    live_stream.close()
    rec1.close(); rec2.close(); rec3.close(); rec4.close(); recL.close();

    #fixing sync of live track:
    print('Syncing up recordings...')
    
    fixL = wave.open('Session/solo.wav', 'rb')               #reopened file this time in read mode
    
    max_samples_in_file = int((loop1_plays + 1) * bars_in_loop1 * beats_per_bar * RATE * (60 / tempo));
    
    solotrack = np.copy(np.frombuffer(fixL.readframes(max_samples_in_file), dtype = np.int16)) #read entire file into list

    solo_file_length = len(solotrack)
    for i in range(solo_file_length - (latency_in_samples)): #shift entire file latency_in_buffers buffers ahead
        solotrack[i] = solotrack[i + (latency_in_samples)]

    fixL.close()
    fixL = wave.open('Session/solo.wav', 'wb')
    fixL.setnchannels(1); fixL.setsampwidth(2); fixL.setframerate(RATE);
    fixL.writeframes(solotrack)
    fixL.close()

pa.terminate()
