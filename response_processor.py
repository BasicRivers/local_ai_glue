import json
import queue
import string

from ollama_generator import generate_response
from sentiment_analysis import analyze_emotion
from text_to_speech import generate_speech
from rag import RagsManager
from settings import status_flags


class ProcessResponse:
    def __init__(self, history_file, sys_prompts_file):
        self.HISTORY_FILE = history_file
        self.SYS_PROMPTS_FILE = sys_prompts_file
        self.Rags_Manager = RagsManager()

    def _load_sys_prompts(self):
        with open(self.SYS_PROMPTS_FILE, "r") as file:
            self.SYSTEM_PROMPTS = file.read()

    # Load conversation history from file (if exists)
    def _load_history(self):
        try:
            with open(self.HISTORY_FILE, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            # Start fresh with system prompt if no file
            self._load_sys_prompts()
            return [
                {
                    'role': 'system',
                    'content': self.SYSTEM_PROMPTS,
                }
            ]
        
    def _remove_punctuation(self,sentence):
        trans = str.maketrans("", "", string.punctuation)
        return sentence.translate(trans)

    # Save conversation history to file
    def save_history(self, messages):
        with open(self.HISTORY_FILE, "w") as f:
            json.dump(messages, f, indent=2)
   
    def process(self, user_input, q:queue.Queue()):
        messages = self._load_history()
        try:
            context = self.Rags_Manager.user_query(user_input)
        except:
            context = ""
            print("RAGs bypassed")
        if len(context) >= 1:
            context = "\n\n".join(context)
            full_prompt = f"""Use the following context to answer the question.
            
            Context:
            {context}
            
            Question:
            {user_input}
            """
        else:
            full_prompt = user_input
            
        messages.append({'role': 'user', 'content': full_prompt})
        full_response = ""
        for sentence in generate_response(messages):
            emotion = analyze_emotion(sentence)
            audio = generate_speech(self._remove_punctuation(sentence))
            full_response+=sentence
            q.put([audio, emotion])

        messages.append({'role': 'assistant', 'content': full_response})
        self.save_history(messages)
        print(full_response)