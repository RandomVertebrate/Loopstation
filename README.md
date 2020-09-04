# Loopstation
Simple 4-Track PC Loopstation with no UI (Console-Based). Uses pyaudio and numpy.
Hemal Patil is making a much cooler, full-featured version of something like this with a GUI, over at HemalPatil/pylooper

With these scripts you can:

1)Live loop audio on 4 overdub-able and mute-able tracks

2)Record your session as five .wav files (4 looping tracks and 1 live track) and mix down to one if necssary using mix.py

You CANNOT:

1)Adjust volume of tracks while Live Looping.

2)Live loop in stereo

3)Select audio device (script uses computer's default audio devices)

INSTRUCTIONS FOR USE:

1)Run setup.py to set parameters (or edit Config/settings.prt)

2)Run LatencyDetector.py for latency measument (optional).

3)Run 4TrackLoopRec.py to start looping:

    enter q, w, e, r to toggle each of four tracks' playback.
    
    enter a, s, d, f to toggle each of four tracks recording (overdubbing).
    
    enter x to exit. If session recording was enabled, wave files will be created in directory Session.

4)Run mix.py to mix wave files down to one track (optional). Mixed track will also be in Session.
