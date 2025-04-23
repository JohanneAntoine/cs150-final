from music21 import *
import os
import generate_markov
import copy
import time
import drums
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
        new_note.pitch.ps += 12
        new_measure.append(new_note)
    return list(new_measure.notes)
        

def crossover(measure1: stream.Measure, measure2: stream.Measure, split_beat=2.0):
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

    
    return list(child1.notes) + list(child2.notes)



"""
final_piece
Input: a filepath, the mode, the tonic, and the number of measures we want to return
Description: Given a generated piece, calculate the fitness of each measure, and sort them in order.
Output: The top n measures
"""
def final_piece(filepath='generated_piece.musicxml', mood='happy', tonic='C', top_n=2, prob=0.5):
    size = 8
    population = []
    generations = 8
    mutated_score = stream.Score()
    mutated_melody = stream.Part()
    final_harmony = stream.Part()
    
    

    for j in range(generations):
        #if not os.path.exists(filepath):
        generate_markov.create_composition(size, prob)
        score_stream = converter.parse(filepath)
        parts = score_stream.parts
        
        
        #os.remove(filepath)
        # score_stream.show('midi')
        # score_stream.show()
        new_population = []
        fitness_measures = []
        for i in range(size):
            composite_measure = stream.Measure(number=i + 1)
            m1 = parts[0].measure(i+1)
            m2 = parts[1].measure(i+1)
            for part in parts:
                part_measures = part.getElementsByClass(stream.Measure)
                if i < len(part_measures):
                    composite_measure.append(part_measures[i].flat.notesAndRests.stream())


            fitness = fitness_function(composite_measure, mood, tonic) + generalFitnessFunction(m1, m2)
            #print(f"Measure {i+1}: Fitness = {fitness}")

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

   

        
        
        chords = []
        skip_next = False
        for i in range(1, len(new_score.parts[0].getElementsByClass('Measure'))+1):
            if skip_next:
                skip_next = False
                continue
            mutation = random()
            m1 = copy.deepcopy(new_score.parts[0].measure(i))
            m2 = new_score.parts[1].measure(i)
            #print(mutation)
            if mutation <= 0.33:
                mutated_melody.append(inversion(m1, m2))
            elif mutation <= 0.67 and i <= len(new_score.parts[0].getElementsByClass('Measure')) - 1:
                mutated_melody.append(crossover(m1, new_score.parts[0].measure(i+1)))
                skip_next = True
            else:
                mutated_melody.append(list(m1.notes))

        for i in range(1, len(new_score.parts[1].getElementsByClass('Measure'))+1):
            m2 = new_score.parts[1].measure(i)
            cMeasure = stream.Measure()
            cMeasure.append(m2.notes[0])
            chords.append(cMeasure)
            

        
        final_harmony.append(chords)
        
    mutated_score.append(mutated_melody.makeMeasures())
    mutated_score.insert(0, final_harmony)
    mutated_score.makeMeasures()

    mutated_score.insert(0, metadata.Metadata())
    mutated_score.metadata.title = "Emotional Jazz"
    mutated_score.metadata.composer = "Eileen Chen, Ezra Jonath, Johanne Antoine"

     # DRUMS
    num_total_measures = len(mutated_score)
    drum_seq = drums.generate_sequence(mood, num_measures=num_total_measures)
    drum_part = drums.sequence_to_stream(drum_seq)

    drum_part.makeMeasures(inPlace=True)
    new_score.append(drum_part)

    #time.sleep(10)
    # mutated_score.show('midi')
    mutated_score.show()


def mutate_measure(measure, mood, tonic='C', mutation_rate=0.3):
    """
    Randomly mutates a measure's notes/chords to conform to the scale for a given mood.
    
    Parameters:
        measure: music21.stream.Measure
        mood: 'happy', 'sad', 'angry' (maps to Lydian, Dorian, Phrygian)
        tonic: tonic root note (default 'C')
        mutation_rate: probability of mutation per note/chord tone (0.0 to 1.0)
        
    Returns:
        A mutated copy of the measure.
    """
    if mood not in mood_mode_map:
        raise ValueError(f"Unsupported mood: {mood}")
    
    #allowed_pitches = [p.name for p in mode_class.getPitches(tonic + '3', tonic + '6')]
    mode_class = mood_mode_map[mood](tonic)
    allowed_pitches = set(p.name for p in mode_class.getPitches())


    mutated = copy.deepcopy(measure)

    for element in mutated.recurse().notesAndRests:
        if isinstance(element, note.Note):
            if random.random() < mutation_rate:
                new_pitch = random.choice(allowed_pitches)
                element.name = new_pitch

        elif isinstance(element, chord.Chord):
            new_pitches = []
            for _ in element.pitches:
                if random.random() < mutation_rate:
                    new_note = random.choice(allowed_pitches)
                    new_pitches.append(new_note)
                else:
                    new_pitches.append(_.name)  # retain existing note
            element.clearPitches()
            for p in new_pitches:
                element.add(pitch.Pitch(p))

    return mutated



if __name__ == "__main__":
    print("Enter a mood (happy, sad, or angry): ")
    mood_options = ['happy','sad','angry']
    mood = input()
    while mood not in mood_options:
        print("Invalid mood, try again.")
        mood = input()
    else:
        print("\nSelected mood:" + mood +".\n")
    
    if mood=='happy':
        prob = 0.6 
    elif mood == 'sad':
        prob=0.3
    else:
        prob = 0.8

    final_piece(mood=mood, prob=prob)
