from music21 import *
from random import random


class instr:
    density: float #probability of dividing
    res: float #shortest note that can be generated
    pat: stream.Stream # to put the notes in


    def __init__(self, density: float, res: float):
        self.density = density
        self.res = res
        self.pat = stream.Stream()



"""
This function will not have rests yet
beats will always be 4
"""
def divvy(ip: instr, low, hi):
    # find midpoint
    mid = (low + hi) / 2
    dur = (hi-low)
    seed = random()
    if (seed < ip.density and (hi-low) > ip.res): #determine if you divide
        divvy(ip, low, mid)
        divvy(ip, mid, hi)
    else:
        ch = note.Note('C', quarterLength=dur)
        #ch.articulations.append(articulations.Staccato())
        ip.pat.insert(low,ch)

sampleMeasure = instr(0.80, 0.25)



divvy(sampleMeasure, 0.0, 4.0)

sampleMeasure.pat.show("text")
sampleMeasure.pat.show()


