import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

from settings import STT

device = "cuda:0" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
model_id = STT
model = AutoModelForSpeechSeq2Seq.from_pretrained(
    model_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
)
model.to(device)
processor = AutoProcessor.from_pretrained(model_id)
pipe = pipeline(
    "automatic-speech-recognition",
    model=model,
    tokenizer=processor.tokenizer,
    feature_extractor=processor.feature_extractor,
    torch_dtype=torch_dtype,
    device=device,
)

def transcribe_audio(audio_data):
    text = pipe(audio_data)["text"]
    return text

def append_text(NOTE_PATH, text): # if the note doesn't exist, create it. if it exists, add a new line and write to it.
    with open(NOTE_PATH, "a") as f:
        f.write(f"\n{text}\n")