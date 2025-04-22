from music21 import *
import os
import generate_markov
import copy
import time
from random import random

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

    elements = list(measure.flat.notesAndRests)

    score = 0
    for i, element in enumerate(elements):
        if isinstance(element, note.Note):
            if element.name in allowed_pitches:
                score += 2
        elif isinstance(element, chord.Chord):
            for n in element.notes:
                if n.name in allowed_pitches:
                    score += 2

        if isinstance(element, note.Note):
            if i + 1 < len(elements):
                next_elem = elements[i + 1]
                if isinstance(next_elem, note.Note):
                    note_interval = interval.Interval(element, next_elem)
                    interval_name = note_interval.name

                    if mood == 'happy':
                        if interval_name == 'M3' or interval_name == 'M-3':
                            score +=1
                        if interval_name == 'P5' or interval_name == 'P-5':
                            score +=1
                    if mood == 'sad':
                        if interval_name == 'm2' or interval_name == 'm-2':
                            score +=1
                        if interval_name == 'M6' or interval_name == 'M-6':
                            score +=1
                    if mood == 'angry':
                        if interval_name == 'm3' or interval_name == 'm-3':
                            score +=1
                        if interval_name == 'm7' or interval_name == 'm-7':
                            score +=1

    return score

def inversion(melody: stream.Measure, harmony: stream.Measure):
    c = harmony.notes[0]
    base_pitch = c.root()
    new_measure = stream.Measure()
    for n in melody.notes:
        p = n.pitch.ps
        distance = p - base_pitch.ps 
        new_note = note.Note(base_pitch.ps-distance)
        new_note.quarterLength = n.quarterLength
        new_measure.append(new_note.transpose('P8'))
    return new_measure
        
def crossover(measure1: stream.Measure, measure2: stream.Measure, split_beat=2.0) -> tuple[stream.Measure, stream.Measure]:
    def split_by_beat(m):
        first_half = stream.Measure(number=m.number)
        second_half = stream.Measure(number=m.number)
        for el in m:
            if isinstance(el, (note.Note, note.Rest, chord.Chord)):
                if el.offset < split_beat:
                    first_half.insert(el.offset, copy.deepcopy(el))
                else:
                    second_half.insert(el.offset - split_beat, copy.deepcopy(el))
        return first_half, second_half
    m1_first, m1_second = split_by_beat(measure1)
    m2_first, m2_second = split_by_beat(measure2)
    child1 = stream.Measure(number=measure1.number)
    child2 = stream.Measure(number=measure2.number)
    # Combine halves
    for el in m1_first:
        child1.insert(el.offset, el)
    for el in m2_second:
        child1.insert(el.offset + split_beat, el)
    for el in m2_first:
        child2.insert(el.offset, el)
    for el in m1_second:
        child2.insert(el.offset + split_beat, el)
    return child1, child2



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

    mutated_score = stream.Score()
    mutated_melody = stream.Part()

    for i in range(1, len(new_score.parts[0].getElementsByClass('Measure'))+1):
        mutation = random()
        m1 = new_score.parts[0].measure(i)
        m2 = new_score.parts[1].measure(i)
        if mutation <= 0.25:
            mutated_melody.append(inversion(m1, m2))
        else:
            mutated_melody.append(m1)

    mutated_score.append(mutated_melody)
    mutated_score.insert(0, new_score.parts[1])

    mutated_score.makeMeasures()

    

    time.sleep(10)
    # mutated_score.show('midi')
    mutated_score.show()

if __name__ == "__main__":
    print("Enter a mood (happy, sad, or angry): ")
    mood_options = ['happy','sad','angry']
    mood = input()
    while mood not in mood_options:
        print("Invalid mood, run again.")
        mood = input()
    else:
        print("\nSelected mood:" + mood +".\n")

    final_piece(mood=mood)
