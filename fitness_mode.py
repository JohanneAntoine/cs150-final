from music21 import *
import os
import generate_markov
import copy
import time

mood_mode_map = {
    'happy': scale.LydianScale,
    'sad': scale.DorianScale,
    'angry': scale.PhrygianScale
}

# Do: FIRST FITNESS FUNCTION: check how well notes match with chord
"""
generalFitnessFunction
Input: A measure of a melody, and a measure of a harmony chord
Description: Compares how many notes in the melody were in the chord
Output: The proportion of similar notes to the number of melody notes
"""
def generalFitnessFunction(melody: stream.Measure, harmony: stream.Measure)->int:
    fitness = 0
    for note in melody.notes:
        if note.pitch.name in list(map(lambda p: p.name, harmony.notes[0].pitches)):
            fitness += 1
    return fitness / len(melody.notes) * 10


"""
fitness_function
Input: A measure, the mood given, and the tonic
Description: check how well measure's notes fit in with mode
Output: The fitness score
"""
def fitness_function(measure, mood, tonic='C'):
    if mood not in mood_mode_map:
        raise ValueError(f"Unsupported mood: {mood}")
    
    mode_class = mood_mode_map[mood](tonic)
    allowed_pitches = set(p.name for p in mode_class.getPitches())

    score = 0
    for element in measure.flat.notesAndRests:
        if isinstance(element, note.Note):
            if element.name in allowed_pitches:
                score += 1
        elif isinstance(element, chord.Chord):
            for n in element.notes:
                if n.name in allowed_pitches:
                    score += 1
    return score

def inversion(melody: stream.Measure, harmony: stream.Measure)->stream.Measure:
    c = harmony.notes[0]
    base_pitch = c.root()
    new_measure = stream.Measure()
    new_melody = stream.Part()
    for note in melody.notes:
        p = note.pitch.ps
        distance = p - base_pitch.ps 
        new_note = note.Note(base_pitch-distance)
        new_melody.append(new_note)
    new_measure.append(new_melody)
    new_measure.append(c)
    return new_measure
        




"""
final_piece
Input: a filepath, the mode, the tonic, and the number of measures we want to return
Description: Given a generated piece, calculate the fitness of each measure, and sort them in order.
Output: The top n measures
"""
def final_piece(filepath='generated_piece.musicxml', mood='happy', tonic='C', top_n=2):
    if not os.path.exists(filepath):
        generate_markov.create_composition()

    score_stream = converter.parse(filepath)
    score_stream.show('midi')
    score_stream.show()

    parts = score_stream.parts
    num_measures = len(parts[0].getElementsByClass(stream.Measure))

    fitness_measures = []
    for i in range(num_measures):
        composite_measure = stream.Measure(number=i + 1)
        m1 = parts[0].measure(i+1)
        m2 = parts[1].measure(i+1)
        for part in parts:
            part_measures = part.getElementsByClass(stream.Measure)
            if i < len(part_measures):
                composite_measure.append(part_measures[i].flat.notesAndRests.stream())


        fitness = fitness_function(composite_measure, mood, tonic) + generalFitnessFunction(m1, m2)
        print(f"Measure {i+1}: Fitness = {fitness}")

        # Store full part-specific measures to rebuild later
        measure_bundle = [copy.deepcopy(part.measure(i + 1)) for part in parts]
        fitness_measures.append((measure_bundle, fitness))

    # Select top-N scoring bundles
    best_measures = sorted(fitness_measures, key=lambda x: x[1], reverse=True)[:top_n]

    # Rebuild parts from top measures
    new_score = stream.Score()
    for p_idx in range(len(parts)):
        new_part = stream.Part()
        new_part.insert(0, parts[p_idx].getInstrument())
        new_part.insert(0, tempo.MetronomeMark(number=80))
        for m_idx, (measure_bundle, _) in enumerate(best_measures):
            m = measure_bundle[p_idx]
            m.number = m_idx + 1
            new_part.append(m)
        new_score.append(new_part)

    time.sleep(15)
    new_score.show('midi')
    new_score.show()

if __name__ == "__main__":
    final_piece(mood='happy')
