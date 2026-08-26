import os

import numpy as np
from kokoro import KPipeline

PATH = os.path.dirname(os.path.abspath(__file__))
pipeline = KPipeline(lang_code='a')

def generate_speech(text):
    audio_arr = np.zeros(0, dtype=np.float32)
    generator = pipeline(text, voice='af_heart')
    file_name = os.path.join(PATH, "speech.wav")
    for gs, ps, audio in generator:
        audio_arr = np.append(audio_arr, audio)
    return audio_arr
