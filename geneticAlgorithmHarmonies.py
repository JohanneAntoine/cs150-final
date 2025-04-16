from music21 import *


def generalFitnessFunction(melody: stream.Measure, harmony: stream.Measure)->int:
    fitness = 0
    for note in melody.notes:
        if note.pitch in harmony.notes[0].pitches:
            fitness += 1
    return fitness / len(melody.notes)

piece = stream.Score()

melody = stream.Part(id="soprano")
harm = stream.Part(id="harmony")

notes = [note.Note('C'), note.Note('D'), note.Note('E'), note.Note('G'), note.Note('E'), note.Note('F'), note.Note('G', quarterLength=2.0)]

for n in notes:
    melody.append(n)

cMaj = chord.Chord('C E G', quarterLength=4.0)
fMaj = chord.Chord('C F A', quarterLength=4.0)
harm.repeatAppend(cMaj, 2)


piece.append(melody)
piece.append(harm)

piece.makeMeasures(inPlace=True)
piece.show()

num_measures = len(piece.parts[0].getElementsByClass('Measure'))


for i in range(1, num_measures+1):
    m1 = piece.parts[0].measure(i)
    m2 = piece.parts[1].measure(i)
    print(generalFitnessFunction(m1, m2))


