import sys
import os
from music21 import *
import random
from collections import defaultdict

folder_path = '/Users/eileenchen/Desktop/jazz-repo'

# Store transitions ((chord1, chord2) -> chord3)
markov_chain = defaultdict(lambda: defaultdict(int))

def extract_chord_label(chord_obj):
    try:
        cs = harmony.chordSymbolFromChord(chord_obj)
        figure = cs.figure
        if figure == "Chord Symbol Cannot Be Identified":
            return None
        return figure
    except Exception:
        return None

for filename in os.listdir(folder_path):
    if filename.endswith('.xml') or filename.endswith('.mxl'):
        file_path = os.path.join(folder_path, filename)
        try:
            score = converter.parse(file_path)

            chordified = score.chordify()
            chords = []

            for c in chordified.recurse().getElementsByClass('Chord'):
                if len(c.pitches) < 2:
                    continue
                while len(c.pitches) > 4:
                    highest = max(c.pitches)
                    c.remove(highest)

                chord_label = extract_chord_label(c)
                if chord_label:
                    chords.append(chord_label)

            # Build second-order transitions
            for i in range(len(chords) - 2):
                prev = (chords[i], chords[i+1])
                next_chord = chords[i+2]
                if next_chord != "Chord Symbol Cannot Be Identified":
                    markov_chain[prev][next_chord] += 1

        except Exception as e:
            print(f"Failed on {filename}: {e}")

output_path = 'chord_markov_output.txt'

with open(output_path, 'w') as f:
    for prev_pair, transitions in markov_chain.items():
        total = sum(transitions.values())
        f.write(f"{prev_pair} →\n")
        for next_chord, count in transitions.items():
            if next_chord == "Chord Symbol Cannot Be Identified":
                continue
            probability = count / total
            f.write(f"    {next_chord}: {probability:.2f}\n")
