import sounddevice as sd
import numpy as np
import queue

class audio_recorder:
    def __init__(self, q:queue.Queue,
                 samplerate=16000,
                 status_flags={"stop":False, "deafen":False, "amplitude": 0.0},
                 rec_props={"rec_channels":1, "max_rec_dur":30, "min_rec_dur":0.5, "callback_interval":0.2,  "silence_dur":5, "silence_threshold_db":-20}):
        self.MIN_ARR_LEN_DETECTED = 50 # minimum amount of datapoints in an array that is required to trigger voice detection.
        self.ARRAY_DEFAULT_VALUE = np.zeros(0, dtype=np.float32)
        
        self.q = q
        self.samplerate = samplerate
        self.status_flags = status_flags
        self.rec_props = rec_props
        self.rec_channels = self.rec_props["rec_channels"]
        self.max_rec_dur = self.rec_props["max_rec_dur"] - self.rec_props["callback_interval"] # subtract 1 callback from the maximum record length to make sure that we are always at least 1 interval away from reaching the max.
        self.max_rec_len = int(self.samplerate*self.max_rec_dur*self.rec_channels) # converted for convenience
        self.min_rec_dur = self.rec_props["min_rec_dur"]
        self.min_rec_len = int(self.samplerate*self.min_rec_dur*self.rec_channels) # converted for convenience
        self.callback_interval = self.rec_props["callback_interval"]
        self.silence_len = self.rec_props["silence_dur"]
        self.silence_threshold_amp = self._db_to_amplitude(self.rec_props["silence_threshold_db"]) # Captured at init. must update on callback.
        self.blocksize = self._seconds_to_blocksize(self.callback_interval, self.samplerate)
        self.reached_silence = False
        self.reached_min_len = False
        self.audio_arr = self.ARRAY_DEFAULT_VALUE.copy()
        self.silence_tracker = 0
        self.record_stream = None
        self.allow_forwarding_arr = False
        self.silence_callbacks_count = 0
    
    def _seconds_to_blocksize(self, sec, samplerate:int):
        return int(sec * samplerate)
    
    def _db_to_amplitude(self, db):
        return 10 ** (-abs(db) / 20)
    
    def forward_array_to_q(self):
        if self.audio_arr.size > 0:
            self.q.put(self.audio_arr)
        
    def audio_callback(self, indata, frames, time, status):
        if not self.status_flags["stop"]:
            if self.allow_forwarding_arr:
                self.forward_array_to_q()
                self.audio_arr = self.ARRAY_DEFAULT_VALUE
                self.allow_forwarding_arr = False
                
            # first we need to check if the mic is not muted
            if not self.status_flags["deafen"]:
                clip_max_amp = np.max(np.abs(indata))
                # recompute the current silence threshold setting in case it changed elsewhere.
                self.silence_threshold_amp = self._db_to_amplitude(self.rec_props["silence_threshold_db"])
                activation_amps_count = (indata > self.silence_threshold_amp).sum()
                # This variable can be seen from outside the class to potentially detect the current volume. It is optional for things like displaying the mic amplitude in real time.
                self.status_flags["amplitude"] = clip_max_amp.copy()
                # then we need to check if there is a significant enough amount of data coming through the microphone
                if activation_amps_count > self.MIN_ARR_LEN_DETECTED:
                    # reset count to avoid non-consecutive silence callbacks
                    self.silence_callbacks_count = 0
                    # there is speech data, append it to an array for now
                    self.audio_arr = np.append(self.audio_arr, indata)
                    # check if we're at max arr len and immediately forward the array to queue if we are
                    if len(self.audio_arr) >= self.max_rec_len:
                        self.allow_forwarding_arr = True
                # this callback was silent but the mic was not muted
                else:
                    self.silence_callbacks_count+=1
            # this callback was silent because the mic was muted
            else:
                self.silence_callbacks_count+=1
                
            # check if the array reached a certain minimum length to be allowed to be forwareded to the queue
            if len(self.audio_arr) >= self.min_rec_len:
                # check if there has been long enough pause of speech by converting callbacks count into seconds and comparing with silence duration object
                if self.silence_callbacks_count*self.callback_interval >= self.silence_len:
                    self.allow_forwarding_arr = True
    
    def start_stream(self):
        self.record_stream = sd.InputStream(
            channels=self.rec_channels,
            samplerate=self.samplerate,
            blocksize=self.blocksize,
            callback=self.audio_callback,
        )
        with self.record_stream:
            print("Recording started...")
            
            while not self.status_flags["stop"]:
                sd.sleep(200)
            sd.stop()
            print("...Recording stopped.")
            
if __name__ == "__main__":
    import threading
    q = queue.Queue()
    record = audio_recorder(q=q)
    recorder_thread = threading.Thread(target=record.start_stream)
    recorder_thread.start()
    input("Press enter to exit")
    record.status_flags["stop"] = True
    recorder_thread.join()