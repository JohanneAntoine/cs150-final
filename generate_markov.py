from music21 import *
import sys
import random
from ast import literal_eval

# CONFIGURATION
MEASURES = 8
TEMPO_BPM = 80
NOTES_PER_MEASURE = 4
RHYTHM = 1.0
MELODY_NOTE_COUNT = MEASURES * NOTES_PER_MEASURE
CHORD_COUNT = MEASURES

# LOAD MARKOV CHAINS
def load_markov_chain(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
    chain = {}
    current_pair = None
    for line in lines:
        line = line.strip()
        if line.endswith('→'):
            current_pair = literal_eval(line[:-1].strip())
            chain[current_pair] = {}
        elif current_pair:
            chord, prob = line.split(':')
            chord = chord.strip()
            prob = float(prob.strip())
            chain[current_pair][chord] = prob
    return chain

melody_chain = load_markov_chain('melody_markov_output.txt')
chord_chain = load_markov_chain('chord_markov_output.txt')

# GENERATE SEQUENCES
def weighted_choice(transitions):
    rand = random.random()
    total = 0
    for choice, prob in transitions.items():
        total += prob
        if rand <= total:
            return choice
    return random.choice(list(transitions.keys()))

def generate_sequence(chain, count):
    state = random.choice(list(chain.keys()))
    sequence = [state[0], state[1]]

    while len(sequence) < count:
        key = (sequence[-2], sequence[-1])
        if key in chain:
            next_element = weighted_choice(chain[key])
        else:
            random_key = random.choice(list(chain.keys()))
            next_element = random.choice(list(chain[random_key].keys()))
        sequence.append(next_element)
    return sequence[:count]

melody_sequence = generate_sequence(melody_chain, MELODY_NOTE_COUNT)
chord_sequence = generate_sequence(chord_chain, CHORD_COUNT)

# COMPOSITION
def create_composition():
    score = stream.Score()
    score.append(tempo.MetronomeMark(number=TEMPO_BPM))

    # Melody Part
    melody_part = stream.Part()
    melody_part.insert(0, instrument.Soprano())
    for pitch_name in melody_sequence:
        try:
            n = note.Note(pitch_name)
            n.quarterLength = RHYTHM
            melody_part.append(n)
        except:
            pass # skip invalid notes

    # Chord Part
    chord_part = stream.Part()
    chord_part.insert(0, instrument.Piano())
    for chord_name in chord_sequence:
        try:
            cs = harmony.ChordSymbol(chord_name)
            ch = chord.Chord(cs.pitches)
            ch.quarterLength = 4.0
            chord_part.append(ch)
        except:
            pass

    score.append(melody_part)
    score.append(chord_part)

    # score.makeMeasures()

    # Show music
    score.show('midi')
    score.show()
    score.show('text')

if __name__ == "__main__":
    create_composition()
