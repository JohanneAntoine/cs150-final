import sys
import os
from music21 import *
import random
from collections import defaultdict

folder_path = '/Users/eileenchen/Desktop/jazz-repo'

# Stores transitions like (prev_note -> next_note)
melody_markov_chain = defaultdict(lambda: defaultdict(int))

def normalize_note(note_obj, key_obj):
    try:
        pitch = note_obj.name  # Get the pitch name (e.g., 'C', 'D#', 'F', etc.)
        return pitch
    except Exception:
        return None


for filename in os.listdir(folder_path):
    if filename.endswith('.xml') or filename.endswith('.mxl'):
        file_path = os.path.join(folder_path, filename)
        try:
            score = converter.parse(file_path)

            # Assuming melody is the highest voice
            melody_part = score.parts[0] if len(score.parts) > 0 else score

            # Extracting melody notes
            melody_notes = []
            for n in melody_part.flatten().notes:  # Use .flatten() instead of .flat
                if isinstance(n, note.Note):  # Ignore rests and chords
                    local_key = n.getContextByClass(key.Key)
                    if not local_key:
                        local_key = melody_part.analyze('key')  # fallback to global key
                    norm_note = normalize_note(n, local_key)
                    if norm_note:
                        melody_notes.append(norm_note)

            # Build second-order transitions for melody
            for i in range(len(melody_notes) - 2):
                prev = (melody_notes[i], melody_notes[i+1])
                next_note = melody_notes[i+2]
                melody_markov_chain[prev][next_note] += 1

        except Exception as e:
            print(f"Failed on {filename}: {e}")

output_path = 'melody_markov_output.txt'

with open(output_path, 'w') as f:
    for prev_pair, transitions in melody_markov_chain.items():
        total = sum(transitions.values())
        f.write(f"{prev_pair} →\n")
        for next_note, count in transitions.items():
            probability = count / total
            f.write(f"    {next_note}: {probability:.2f}\n")


# Function to generate a melody based on the Markov chain
def generate_melody(start_note, num_notes=20):
    melody = [start_note]
    for _ in range(num_notes - 1):
        prev = tuple(melody[-2:])  # Get the last two notes
        next_note_choices = melody_markov_chain.get(prev, {})
        if not next_note_choices:
            break  # No more transitions possible
        # Choose the next note based on the transition probabilities
        total = sum(next_note_choices.values())
        r = random.uniform(0, total)
        cumulative_prob = 0
        for next_note, count in next_note_choices.items():
            cumulative_prob += count
            if cumulative_prob >= r:
                melody.append(next_note)
                break
    return melody
