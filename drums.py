from music21 import *
import random


# General MIDI Drum Map 
PERC_MAP = {
    'K': 36,  # Kick
    'S': 38,  # Snare
    'H': 42,  # Closed Hi-Hat
    'R': None  # Rest
}


# Groove templates by emotion 
GROOVE_RULES = {
    'happy': [
        "H H S H", "H R H S", "H S H K", "H H K S"
    ],
    'sad': [
        "H R H R", "H R S R", "R H R S"
    ],
    'angry': [
        "K S K S", "H S K S", "K K S S", "K S H K"
    ]
}

# Helper Functions

def get_swing_duration(is_first_in_pair):
    base = 0.67 if is_first_in_pair else 0.33
    return base + random.uniform(-0.015, 0.015)  # micro jitter

def get_velocity(symbol, position):
    if symbol == 'H':
        return random.randint(60, 70)
    elif symbol == 'S':
        return 85 if position % 4 == 1 else random.randint(60, 70)  # backbeat
    elif symbol == 'K':
        return random.randint(75, 90)
    return 64

def generate_sequence(emotion, num_measures=4):
    grammar = GROOVE_RULES.get(emotion, GROOVE_RULES[emotion])
    sequence = []

    for _ in range(num_measures):
        pattern = random.choice(grammar)
        sequence.extend(pattern.split())

    return sequence


# Stream Conversion
def sequence_to_stream(seq, swing=True, for_score=False):
    part = stream.Part()
    part.id = "Percussion"
    instr = instrument.Woodblock()  # Generic unpitched
    instr.midiChannel = 9  # Channel 10 for percussion
    part.insert(0, instr)

    if for_score:
        part.insert(0, expressions.TextExpression("Swing feel"))
        time = 0.0

    is_first = True
    time = 0.0

    for i, symbol in enumerate(seq):
        if swing:
            dur = 0.67 if is_first else 0.33
            is_first = not is_first
        else:
            dur = 0.5

        if symbol == 'R':
            n = note.Rest(quarterLength=dur)
        else:
            midi_pitch = PERC_MAP[symbol]
            n = note.Note()
            n.pitch.midi = midi_pitch
            n.duration.quarterLength = dur
            n.volume.velocity = 75
            n.isPercussion = True
            n.storedInstrument = instr
            n.channel = 9  # Channel 10 (zero indexed)

        part.insert(time, n)
        time += dur

    return part


def export_midi(part, filename="swing_groove.mid"):
    mf = midi.translate.streamToMidiFile(part)
    mf.open(filename, 'wb')
    mf.write()
    mf.close()
    print(f"Midi exported: {filename}")

def export_score(part, filename="swing_score.xml"):
    # Add metadata so MuseScore opens cleanly
    score = stream.Score()
    score.append(part)
    score.metadata = metadata.Metadata()
    score.metadata.title = "Swing Percussion"
    score.metadata.composer = "Ezra"
    score.write("musicxml", fp=filename)
    print(f"MusicXML score exported: {filename}")

# RUN STUFF

# Example: Generate an angry swing groove
emotion = 'angry'
sequence = generate_sequence(emotion, num_measures=4)

# Create versions
midi_part = sequence_to_stream(sequence, swing=True, for_score=False)
score_part = sequence_to_stream(sequence, swing=False, for_score=True)

# Export both
export_midi(midi_part, "swing_groove.midi")
export_score(score_part, "swing_score.xml")


