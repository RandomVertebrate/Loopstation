print('Collecting files...')

import wave
import numpy as np

f_out = wave.open('Session/mono_mix.wav', 'wb')

f = [wave.open('Session/track1.wav', 'rb'),
     wave.open('Session/track2.wav', 'rb'),
     wave.open('Session/track3.wav', 'rb'),
     wave.open('Session/track4.wav', 'rb'),
     wave.open('Session/solo.wav', 'rb')]

params = f[4].getparams() #arbitrary choice; everything except length is the same for all files
length = min(f[0].getnframes(), f[1].getnframes(), f[2].getnframes(), f[3].getnframes(), f[4].getnframes())
#output track will be as long as shortest input track to prevent index problems
f_out.setparams(params)
f_out.setnframes(length)

theo_max = 2**15 - 2 #max posible absolute value of a sample

gain = 1

max_peak_sum = 0

outputaudio = np.zeros([length], dtype = np.int16)
inputaudio = np.zeros([5, length], dtype = np.int16)

for i in range(5): #reading all files into arrays
    inputaudio[i] = np.copy(np.frombuffer(f[i].readframes(length), dtype = np.int16))

#mixing:
print('Mixing...')
tmp_mix = inputaudio[0] + inputaudio[1] + inputaudio[2] + inputaudio[3] + inputaudio[4]
max_peak_sum = np.max(tmp_mix)

gain = theo_max / max_peak_sum

#amplifying:
print('Amplifying...')
outputaudio = np.array((tmp_mix * gain), dtype = np.int16)

f_out.writeframes(outputaudio)

print('Done.')

f[0].close()
f[1].close()
f[2].close()
f[3].close()
f[4].close()
f_out.close()
