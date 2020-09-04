f = open('Config/settings.prt', 'r')
parameters = f.readlines()
while (len(parameters) < 12):
    parameters.append('\n')
f.close()

if (input('Change Loop Settings? (y/n): ') == 'y'):
    parameters[4] = input('Enter Tempo in BPM: ') + '\n'
    parameters[5] = input('How Many Beats per Bar? : ') + '\n'
    parameters[6] = input('Enter Length of Loop 1 in Bars : ') + '\n'
    parameters[7] = input('How Many Bars of Count-in? : ') + '\n'
    parameters[8] = input('Enter Length of Loop 2 Relative to Loop 1 (1, 2, 3 or 4): ') + '\n'
    parameters[9] = input('Enter Length of Loop 3 Relative to Loop 1 (1, 2, 3 or 4): ') + '\n'
    parameters[10] = input('Enter Length of Loop 4 Relative to Loop 1 (1, 2, 3 or 4): ') + '\n'

if (input('Change Audio Settings? (y/n): ') == 'y'):
    parameters[0] = input('Enter Sample Rate in Hz (Safe Choices 44100 and 48000): ') + '\n'
    parameters[1] = input('Enter Buffer Size (Typical 256, 512, 1024) : ') + '\n'
    parameters[2] = input('Enter Latency Correction in milliseconds : ') + '\n'
    parameters[3] = input('Enter Length of Metronome Beeps in Buffers (Typical 1-5) : ') + '\n'

    
if (input('Record session? (y/n): ') == 'y'):
    parameters[11] = '1'
else:
    parameters[11] = '0'


f = open('Config/settings.prt', 'w')
for i in range(12):
    f.write(parameters[i])
f.close()
