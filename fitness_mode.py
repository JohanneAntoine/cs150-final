import sys
from music21 import *
import os
import generate_markov
import copy
import time
import drums
import random
import pickle 

mood_mode_map = {
    'happy': scale.LydianScale,
    'sad': scale.DorianScale,
    'angry': scale.PhrygianScale
}

instrument_map = {
    'happy': instrument.AltoSaxophone(),
    'sad': instrument.Piano(),
    'angry': instrument.Trumpet()
}

tempo_map = {
    'happy': 100,
    'sad': 60,
    'angry': 130
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


"""
inversion
Input: a measure containing the melody, and a measure containing the harmony chord
Description: Taking the root of the harmony, invert the melody based off of the distance from the root
Output: A list of notes indicating the new melody
"""
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
        
"""
crossover
Input: Two measures, and a float indicating where we will make the split
Description: Split the measures in half, and then cross them over
Output: list of notes indicating a new melody
"""
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
def final_piece(filepath='generated_piece.musicxml', mood='happy', tonic='C', top_n=2, prob=0.5, output_mode="midi"):
    size = 8

    generations = 8
    mutated_score = stream.Score()
    mutated_melody = stream.Part()
    final_harmony = stream.Part()
    
    instrument_for_mood = instrument_map[mood]  # Get the instrument from the map
    tempo_for_mood = tempo_map[mood]  # Get the tempo from the map
    

    for j in range(generations):
        #if not os.path.exists(filepath):
        generate_markov.create_composition(size, prob)
        score_stream = converter.parse(filepath)
        parts = score_stream.parts
        
        
        #os.remove(filepath)
        # score_stream.show('midi')
        #score_stream.show("text")

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

        # Perform mating & mutations
        for i in range(1, len(new_score.parts[0].getElementsByClass('Measure'))+1):
            print("i = ", i)
            # if skip_next:
            #     skip_next = False
            #     continue
            mutation = random.random()
            m1 = copy.deepcopy(new_score.parts[0].measure(i))
            m2 = new_score.parts[1].measure(i)
            if mutation <= 0.25:
                mutated_melody.append(inversion(m1, m2))
                print("inversion")
            # perform multiple-point mutation
            elif mutation >= 0.25 and mutation <= 0.50:
                print("mutationated")
                mutated = mutate_measure(m1, mood, tonic, mutation_rate=0.5)
                mutated_melody.append(mutated)
            # perform crossover 
            elif mutation <= 0.80 and i <= len(new_score.parts[0].getElementsByClass('Measure')) - 1:
                mutated_melody.append(crossover(m1, new_score.parts[0].measure(i+1)))
                print ("crossover")
                break
            else:
                mutated_melody.append(list(m1.notes))

        for i in range(1, len(new_score.parts[1].getElementsByClass('Measure'))+1):
            m2 = new_score.parts[1].measure(i)
            cMeasure = stream.Measure()
            cMeasure.append(m2.notes[0])
            chords.append(cMeasure)

        # ## ADDED    
        # for i in range(len(mutated_melody)):
        #     m2 = new_score.parts[1].measure(min(i + 1, len(new_score.parts[1].getElementsByClass('Measure'))))
        #     cMeasure = stream.Measure()
        #     cMeasure.append(copy.deepcopy(m2.notes[0]))
        #     chords.append(cMeasure)


        print("finished gen")
        final_harmony.append(chords)
        
       # Set instrument and tempo for melody part
    mutated_melody.insert(0, instrument_for_mood)
    mutated_melody.insert(0, tempo.MetronomeMark(number=tempo_for_mood))

    # Set a default instrument (e.g., Piano) for harmony if you want
    final_harmony.insert(0, instrument.Piano())
    final_harmony.insert(0, tempo.MetronomeMark(number=tempo_for_mood))

    # for i, m in enumerate(mutated_melody):
    #     harmony_note = chord.Chord([m.notes[0].name]) if m.notes else note.Rest()
    #     harmony_measure = stream.Measure(number=i + 1)
    #     harmony_measure.append(harmony_note)
    #     final_harmony.append(harmony_measure)

    print("melody len ", len(mutated_melody.getElementsByClass(stream.Measure)))
    print("hamony len", len(final_harmony.getElementsByClass(stream.Measure)))
    for _ in range(5):
        last_measure = mutated_melody.getElementsByClass(stream.Measure)[-1]
        mutated_melody.remove(last_measure)

    mutated_score.append(mutated_melody.makeMeasures())
    mutated_score.insert(0, final_harmony)
    mutated_score.makeMeasures()

    mutated_score.insert(0, metadata.Metadata())
    mutated_score.metadata.title = "Emotional Jazz"
    mutated_score.metadata.composer = "Eileen Chen, Ezra Jonath, Johanne Antoine"

     # DRUMS
    num_total_measures = size * 4
    # drum_seq = drums.generate_sequence(mood, num_measures=num_total_measures)
    #num_measures=len(mutated_melody.getElementsByClass(stream.Measure))

    #ADDED
    drum_seq = drums.generate_sequence(mood, num_measures=num_total_measures)

    drum_part = drums.sequence_to_stream(drum_seq)

    # drum_seq = drums.generate_sequence(mood, num_measures=len(mutated_melody))
    # drum_part = drums.sequence_to_stream(drum_seq, swing=True)
    # drum_part.makeMeasures(inPlace=True)

    drum_part.makeMeasures(inPlace=True)
    mutated_score.insert(0,drum_part)

    #time.sleep(10)
    mutated_score.show('midi')
    preloaded_file = open('examplePickle', 'ab')
    preloaded_notes = pickle.dump(mutated_score, preloaded_file)
    preloaded_file.close()
    #mutated_score.show("text")


"""
mutate_measure
Input: measure: music21.stream.Measure, mood: 'happy', 'sad', 'angry' (maps to Lydian, Dorian, Phrygian), tonic: tonic root note (default 'C'), mutation_rate: probability of mutation per note/chord tone (0.0 to 1.0)
Description:  Randomly mutates a measure's notes/chords to conform to the scale for a given mood.
Output: A mutated copy of the measure.
"""
def mutate_measure(measure, mood, tonic='C', mutation_rate=0.3):
    
    if mood not in mood_mode_map:
        raise ValueError(f"Unsupported mood: {mood}")
    
    #allowed_pitches = [p.name for p in mode_class.getPitches(tonic + '3', tonic + '6')]
    mode_class = mood_mode_map[mood](tonic)
    # allowed_pitches = set(p.name for p in mode_class.getPitches())
    allowed_pitches = [p for p in mode_class.getPitches()]

    mutated = copy.deepcopy(measure)
    print("Mutated")
    mutated.show("text")
    mutated_result = stream.Measure()

    for element in mutated.notes:
        if random.random() < mutation_rate:
            new_pitch = random.choice(allowed_pitches)
            element.pitch = new_pitch
        mutated_result.append(element)

        # elif isinstance(element, chord.Chord):
        #     new_pitches = []
        #     for _ in element.pitches:
        #         if random.random() < mutation_rate:
        #             new_note = random.choice(allowed_pitches)
        #             new_pitches.append(new_note)
        #         else:
        #             new_pitches.append(_.name)  # retain existing note
        #     element.clearPitches()
        #     for p in new_pitches:
        #         element.add(pitch.Pitch(p))

    print("Result")
    mutated_result.show("text")
    print(list(mutated_result.notes))
    return list(mutated_result.notes)



if __name__ == "__main__":
    if ("-p" in sys.argv) and os.path.exists("examplePickle"):
        preloaded_file = open('examplePickle', 'rb')
        preloaded_notes = pickle.load(preloaded_file)
        finalStream = stream.Stream()
        finalStream.append(preloaded_notes)
        preloaded_file.close()
    else:
    
    if ("-m" in sys.argv):
        output_mode = "midi"
    elif ("-s" in sys.argv):
       output_mode = "score"
    else:
        output_mode = "text"

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

    final_piece(mood=mood, prob=prob, output_mode=output_mode)
