import os

from ollama import chat

from settings import LLM

sentence_enders = [".", ",", ")", "\n", "!", "?"]
model = LLM

def split_by_punct(text, sentence_enders):
    result = []
    current = ""
    i = 0
    while i < len(text):
        ch = text[i]
        # Skip leading punctuation or spaces before starting a new segment
        if not current and (ch in sentence_enders or ch.isspace()):
            i += 1
            continue
        current += ch
        # If this char is a punctuation ender, finalize the segment
        if ch in sentence_enders:
            # Only append if it contains actual text (not just punctuation/spaces)
            if any(c.isalnum() for c in current):
                result.append(current.strip())
            current = ""
        i += 1
    # Add leftover text without punctuation
    if current.strip():
        result.append(current.strip())
    return result
    
def generate_response(messages):
    buffer = ""
    for chunk in chat(model, messages=messages, stream=True):
        response = chunk.get("message", {}).get("content", "")
        buffer += response
        segments = split_by_punct(buffer, sentence_enders)
        # If we got more than one segment or exactly one complete segment
        if segments:
            # Emit all complete sentences
            for seg in segments[:-1]:
                yield seg
            # The last segment might be incomplete, we store it
            buffer = segments[-1]
    # After streaming ends, output final leftover
    if buffer.strip():
        yield buffer
        
if __name__ == "__main__":
    messages=[
        {
        'role': 'user',
        'content': 'Why is the sky blue?',
        }
        ]
    for chunk in generate_response(messages):
        print(chunk)