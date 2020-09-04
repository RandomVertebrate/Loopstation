import pyaudio
import numpy as np
import time

settings_file = open('Config/settings.prt', 'r')
parameters = settings_file.readlines()
settings_file.close()

RATE = int(parameters[0]) #sample rate
CHUNK = int(parameters[1]) #buffer size
FORMAT = pyaudio.paInt16
CHANNELS = 1

CLIPLENGTH = 100 #probably ok as constant.

click_ang_fr = 0.5 #angular frequency of test click in radians per sample. Probably ok as constant.

pa = pyaudio.PyAudio()

silence = np.zeros(CHUNK, dtype = np.int16)

click = np.zeros(CHUNK, dtype = np.int16)
for i in range(CHUNK):
    click[i] = 32767 * (np.sin(click_ang_fr * i))                   #creating sine wave in click buffer

testclip = np.zeros([CLIPLENGTH, CHUNK], dtype = np.int16)          #stores data recorded during test

clicknesses = np.zeros([CLIPLENGTH], dtype = np.single)             #for storing RMS of click frequency component for each buffer in testclip

clickest_buffer = 0                                                 #for storing index of most click-like buffer

def clickness(buffer):                                              #calculates RMS (with resonant filter at click frequency) of a buffer
    sincomp = 0.0
    coscomp = 0.0
    value = 0.0
    for i in range(CHUNK):                                          #summation of sample[i] * sin(wi) over buffer
        sincomp = sincomp + buffer[i] * (np.sin(click_ang_fr * i))
    for i in range(CHUNK):                                          #summation of sample[i] * cos(wi) over buffer
        coscomp = coscomp + buffer[i] * (np.cos(click_ang_fr * i))
    value = (sincomp**2 + coscomp**2) / CHUNK
    return (value**(1/2))

current_buffer = -1
#index for iteration through testclip within stream callback function.
#will be incremented before it is used


#following stream callback function, plays 1 buffer of click followed by CLIPLENGTH - 1 buffers of silence, and simultaneously records testclip.
def test_callback(in_data, frame_count, time_info, status):
    global clicknesses
    global click
    global testclip
    global current_buffer

    current_buffer = current_buffer + 1

    if (current_buffer == CLIPLENGTH):
        return(silence, pyaudio.paComplete)

    testclip[current_buffer, :] = np.frombuffer(in_data, dtype = np.int16)    
    
    if (current_buffer == 0):
        return(click, pyaudio.paContinue)
    else:
        return(silence, pyaudio.paContinue)

test_stream = pa.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    output=True,
    frames_per_buffer = CHUNK,
    start = False,
    stream_callback = test_callback
)

input('Make sure any hardware monitoring is turned OFF, then press Enter')

print('Hold speaker and microphone close together...')

time.sleep(4)

print('Testing...')

time.sleep(0.5)

test_stream.start_stream()
while(test_stream.is_active()):
    time.sleep(0.1)

print('Calculating latency...')

for i in range(CLIPLENGTH): #calculating clicknesses
    clicknesses[i] = clickness(testclip[i, :])

for i in range(CLIPLENGTH): #finding index of clickest buffer
    if (clicknesses[i] > clicknesses[clickest_buffer]):
        clickest_buffer = i

mean_clickness = 0
for i in range(CLIPLENGTH): #calculating mean clickness of buffers in testclip
    mean_clickness = mean_clickness + clicknesses[i]
mean_clickness = mean_clickness / CLIPLENGTH

standard_deviation = 0
for i in range(CLIPLENGTH): #calculating standard deviation in clickness of buffers in testclip
    standard_deviation = standard_deviation + (clicknesses[i] - mean_clickness)**2
standard_deviation = standard_deviation / CLIPLENGTH
standard_deviation = standard_deviation**(1/2)

latency_in_milliseconds = int((clickest_buffer * CHUNK / RATE) * 1000)

if (abs(clicknesses[clickest_buffer] - mean_clickness) > 7 * (standard_deviation)): #test for statistical significance
    print('Measured latency is ' + str(clickest_buffer) + ' buffers with buffer size ' + str(CHUNK) + ' at sample rate ' + str(RATE / 1000) + 'kHz')
    print('i.e. about ' + str(latency_in_milliseconds) + ' milliseconds.')
    if (input('Set measured value as latency value for looping? (y/n): ') == 'y'):
        settings_file = open('Config/settings.prt', 'r')
        parameters = settings_file.readlines()
        settings_file.close()
        settings_file = open('Config/settings.prt', 'w')
        parameters[2] = str(latency_in_milliseconds) + '\n'
        for i in range(12):
            settings_file.write(parameters[i])
        settings_file.close()
        print('Done.')
else:
    print('Test not conclusive, please\na) Move mic and speaker closer together\nb) Turn up volume\nc) Move to a quieter location')

input('Press Enter')
