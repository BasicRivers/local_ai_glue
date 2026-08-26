import os
# os.environ["HF_HUB_OFFLINE"] = "1" # Uncomment this line to run the models fully locally without checking on Huggingface updates first. The models need to be cached locally first by running them once.
import threading
import time
import queue

import sounddevice as sd
from PySide6.QtWidgets import QApplication

from response_processor import ProcessResponse
from record import audio_recorder
from speech_to_text import transcribe_audio
from ui import MainWindow
from settings import KOKORO_SAMPLERATE, WHISPERAI_SAMPLERATE, LISTENING_TIMEOUT, status_flags, wake_keywords, record_props, animation_duration, HISTORY_FILE, SYS_PROMPTS_FILE

chat = {"user": "", "context":[]}
# this queue will contain the audio data that comes in from the mic. we want to take the latest data if we were not listening.
q_in = queue.Queue() if status_flags["listening"] else queue.LifoQueue()
# this queue will contain the text response of the llm and sentiment analysis of that text.
q_out = queue.Queue()
response = ProcessResponse(HISTORY_FILE, SYS_PROMPTS_FILE)
# record = audio_recorder(q=q_in, samplerate=WHISPERAI_SAMPLERATE, status_flags=status_flags, min_rec_len=0.5)
record = audio_recorder(q=q_in, samplerate=WHISPERAI_SAMPLERATE, status_flags=status_flags, rec_props=record_props)

def _reset_q_in_properties():
    q_in = queue.Queue() if status_flags["listening"] else queue.LifoQueue()

def transcribe_loop(q_in):
    while not status_flags["stop"] or q_in.qsize() > 0:
        if q_in.qsize() > 0:
            print("Transcribing clip...")
            audio_data = q_in.get()
            text = transcribe_audio(audio_data)
            chat["user"]+=text
            print("Clip transcribed!")
            print(f"Queued clips: {q_in.qsize()}")
        else:
            time.sleep(2)

# if something is in the user chat object, send it to the language model and get the response and emotion added to the output queue
def input_handler(out_queue):
    timeout = LISTENING_TIMEOUT
    timer_start = time.time()
    while not status_flags["stop"]:
        if chat["user"] != "":
            if status_flags["listening"]:
                # Reset the timer whenever there is a new message
                timer_start = time.time()
                response.process(chat["user"], out_queue)
                chat["user"] = ""
            # if we're not listening already, but a keyword is spoken
            elif any(keyword.lower() in chat["user"].lower() for keyword in wake_keywords):
                timer_start = time.time()
                status_flags["listening"] = True
                _reset_q_in_properties()
                print("now listening")
                window.reset_animation()
                chat["user"] = "" # we don't need the model to respond to a wake keyword, we just want to activate it
            # if the user speaks and it doesn't contain any keywords and the model wasn't listening, we can ignore it
            else:
                chat["user"] = ""
        else:
            time.sleep(2)
            if time.time() - timer_start >= timeout:
                timer_start = time.time()
                print("no longer listening")
                status_flags["listening"] = False
                _reset_q_in_properties()
                window.reset_animation()
                
def response_handler(q_out):
    while not status_flags["stop"] or q_out.qsize() > 0:
        if q_out.qsize() > 0:
            audio, emotion = q_out.get()
            status_flags["emotion"] = emotion
            window.images = window.update_current_emotion(emotion)
            status_flags["speaking"] = True
            sd.play(audio, samplerate=KOKORO_SAMPLERATE, blocking=not status_flags["stop"]) # blocking is only True if the program hasn't been stopped, otherwise it can be interrupted
            status_flags["speaking"] = False
            window.reset_animation()
        else:
            time.sleep(2)
    sd.stop()

def animation():
    while not status_flags["stop"]:
        # window.reset_animation()
        if status_flags["speaking"]:
            window.toggle_animation()
            time.sleep(animation_duration)
        else:
            time.sleep(0.1)
        
app = QApplication()
window = MainWindow(status_flags, HISTORY_FILE)

recorder_thread = threading.Thread(target=record.start_stream)
recorder_thread.start()
transcribe_thread = threading.Thread(target=transcribe_loop, args=(q_in,))
transcribe_thread.start()
generator_thread = threading.Thread(target=input_handler, args=(q_out,))
generator_thread.start()
speaker_thread = threading.Thread(target=response_handler, args=(q_out,))
speaker_thread.start()
animation_thread = threading.Thread(target=animation)
animation_thread.start()

window.show()
app.exec()

status_flags["stop"] = True
status_flags["listening"], status_flags["speaking"] = False, False
sd.stop()
q_in.queue.clear()
q_out.queue.clear()
response.Rags_Manager.kill_DB_client()
speaker_thread.join()
animation_thread.join()
recorder_thread.join()
transcribe_thread.join()
generator_thread.join()