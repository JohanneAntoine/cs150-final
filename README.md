1. Names and UTLNs:
Johanne Antoine (jantoi01)
Eileen Chen (echen23)
Ezra Jonah (sjonat01)

2. How to run our code:
Run the program to generate sheet music: python fitness_mode.py -s 
Run the program to generate midi: python fitness_mode.py -m 

3. High-level summary of compositional approach:
Our composition aims to algorithmically generate emotionally-driven jazz music
by combining several techniques. We begin by mapping emotional categories 
(happiness, sadness, and anger) to musical modes and stylistic characteristics. 
Rhythm is generated using Stochastic Binary Subdivision, where base durations 
are recursively and probabilistically split depending on the emotional context. 
Melody improvisation follows using second-order Markov chains trained on a jazz 
database. Chords are also generated using separate second-order Markov chains. 
Next, we employ genetic algorithms to select measures where the melody and 
accompaniment align well, as well as those that match the assigned emotion, 
and then mutate them to create new variations.
