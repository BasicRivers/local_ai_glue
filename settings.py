LLM="llama3.2:1b"
SENTIMENT_ANALYSIS="boltuix/bert-emotion"
STT="openai/whisper-base.en"
RAGS="sentence-transformers/all-MiniLM-L6-v2"

HISTORY_FILE = "./conversation_history.json"
SYS_PROMPTS_FILE= "./system_prompts.txt"
RAG_PATHS = {
    "SOURCE_DATA":"./RAG_SOURCE",
    "VECTOR_DB_PATH":"./DATABASES",
    "PDF_COLLECTION":"./Vectorized_PDFs"
}

# The samplerate on which Kokoro was trained, the text-to-speech model.
KOKORO_SAMPLERATE = 24000
# The samplerate on which WhisperAI was trained, the speech-to-text model.
WHISPERAI_SAMPLERATE = 16000
# How long the model waits after the last message before it stops listening.
LISTENING_TIMEOUT = 180

animation_duration = 0.075
wake_keywords = ["computer", "wake up"]
status_flags = {"stop": False, "deafen": False, "silence_threshold": -25, "emotion": "neutral", "speaking": False, "listening": False, "amplitude":0.0}
record_props = {"rec_channels":1, "max_rec_dur":30, "min_rec_dur":0.5, "callback_interval":0.2,  "silence_dur":5, "silence_threshold_db":-20}