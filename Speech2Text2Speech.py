#!/usr/bin/env python

"""Google Cloud Speech API sample application using the streaming API.

NOTE: This module requires the additional dependency `pyaudio`. To install
using pip:

    pip install pyaudio

Example usage:
    python transcribe_streaming_mic.py
"""

# [START import_libraries]
from __future__ import division

import re
import sys
import time
import itertools

from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types
import pyaudio
from six.moves import queue
# [END import_libraries]

import keyboard

# Colors for printing
import colorama
colorama.init()

import pyttsx
# Initialize voice engine for tts
voiceEngine = pyttsx.init()
# Get list of OS installed voices
voices = voiceEngine.getProperty('voices')
print("Available voices: ")
for voice in voices: print(colorama.Fore.CYAN + colorama.Style.BRIGHT + voice.name + colorama.Style.RESET_ALL)
# Given a list of installed voices, set one as the engine voice
voiceEngine.setProperty('voice', voices[1].id) # initial 2 voices installed with english windows, set to Zira
# Set voice global variable for thread to change
voiceID = voices[1].id
# Set mute global for thread and listen global
playVoice = True
isListening = True
rtcRedo = False

# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms


class MicrophoneStream(object):
    """Opens a recording stream as a generator yielding the audio chunks."""
    def __init__(self, rate, chunk):
        self._rate = rate
        self._chunk = chunk

        # Create a thread-safe buffer of audio data
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            # The API currently only supports 1-channel (mono) audio
            # https://goo.gl/z757pE
            channels=1, rate=self._rate,
            input=True, frames_per_buffer=self._chunk,
            # Run the audio stream asynchronously to fill the buffer object.
            # This is necessary so that the input device's buffer doesn't
            # overflow while the calling thread makes network requests, etc.
            stream_callback=self._fill_buffer,
        )

        self.closed = False

        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        # Signal the generator to terminate so that the client's
        # streaming_recognize method will not block the process termination.
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        """Continuously collect data from the audio stream, into the buffer."""
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            # Use a blocking get() to ensure there's at least one chunk of
            # data, and stop iteration if the chunk is None, indicating the
            # end of the audio stream.
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            # Now consume whatever other data's still buffered.
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b''.join(data)
# [END audio_stream]


def listen_print_loop(responses, oldTime):
    """Iterates through server responses and prints them.

    The responses passed is a generator that will block until a response
    is provided by the server.

    Each response may contain multiple results, and each result may contain
    multiple alternatives; for details, see https://goo.gl/tjCPAU.  Here we
    print only the transcription for the top alternative of the top result.

    In this case, responses are provided for interim results as well. If the
    response is an interim one, print a line feed at the end of it, to allow
    the next result to overwrite it, until the response is a final one. For the
    final one, print a newline to preserve the finalized transcription.
    """
    num_chars_printed = 0
    for response in responses:
        
        # Do we still need to have Google listen?
        if not isListening:
            break
        # How to deal with RTC timeouts?
        if time.time() > oldTime + 60:
            rtcRedo = True
            print("Resetting connection to avoid RTC Timeout...")
            break
        else:
            rtcRedo = False
        
        if not response.results:
            continue

        # The `results` list is consecutive. For streaming, we only care about
        # the first result being considered, since once it's `is_final`, it
        # moves on to considering the next utterance.
        result = response.results[0]
        if not result.alternatives:
            continue

        # Display the transcription of the top alternative.
        transcript = result.alternatives[0].transcript

        # Display interim results, but with a carriage return at the end of the
        # line, so subsequent lines will overwrite them.
        #
        # If the previous result was longer than this one, we need to print
        # some extra spaces to overwrite the previous result
        overwrite_chars = ' ' * (num_chars_printed - len(transcript))

        if not result.is_final:
            sys.stdout.write(transcript + overwrite_chars + '\r')
            sys.stdout.flush()

            num_chars_printed = len(transcript)

        else:
            print(transcript + overwrite_chars)
            
            # Check for a change in voice engine voice
            voiceEngine.setProperty('voice', voiceID)
            # Read message using tts
            readUsingTTS(transcript)              

            # Exit recognition if any of the transcribed phrases could be
            # one of our keywords.
            if re.search(r'\b(exit|quit)\b', transcript, re.I):
                print('Exiting..')
                break

            num_chars_printed = 0
            
            
def readUsingTTS(ttsMessage):
    # Play the tts message using voice engine
    if playVoice:
        voiceEngine.say(ttsMessage)
        voiceEngine.runAndWait() 
    return
    
def setupHotkeys():
    keyboard.add_hotkey('q', muteOutputTTS)
    keyboard.add_hotkey('z', closeAnalysisConnection)
    for number in range(0,len(voices)):
        keyboard.add_hotkey(str(number), changeVoice, args=[number])
    return
    
def muteOutputTTS():
    global playVoice
    playVoice = not playVoice
    print(colorama.Fore.YELLOW + colorama.Style.BRIGHT + "Microphone: " + str(playVoice) + colorama.Style.RESET_ALL)
    return
    
def closeAnalysisConnection():
    global isListening
    isListening = not isListening
    print(colorama.Fore.RED + colorama.Style.BRIGHT + "Listening: " + str(isListening) + colorama.Style.RESET_ALL)
    return
    
def changeVoice(number):
    global voiceID
    voices = voiceEngine.getProperty('voices')
    voiceID = voices[number].id
    print(colorama.Fore.CYAN + colorama.Style.BRIGHT + "Voice changed to: " + voices[number].name + colorama.Style.RESET_ALL)
    return

def main():
    # See http://g.co/cloud/speech/docs/languages
    # for a list of supported languages.
    language_code = 'en-US'  # a BCP-47 language tag
    
    setupHotkeys()
    
    oldTime = time.time()

    while(True):
        if isListening or rtcRedo:

            client = speech.SpeechClient()
            #print(client)
            print("Connected: Okay, Start Talking!")
            config = types.RecognitionConfig(
                encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=RATE,
                language_code=language_code)
            streaming_config = types.StreamingRecognitionConfig(
                config=config,
                interim_results=True)

            with MicrophoneStream(RATE, CHUNK) as stream:
                audio_generator = stream.generator()
                requests = (types.StreamingRecognizeRequest(audio_content=content)
                            for content in audio_generator)

                responses = client.streaming_recognize(streaming_config, requests)

                # Now, put the transcription responses to use.
                listen_print_loop(responses, oldTime)
                
        else:
            #print("Not Listening...")
            spinner = itertools.cycle(['-', '/', '|', '\\'])
            while not isListening:
                sys.stdout.write('Not Listening... ' + spinner.next() + '\r')
                sys.stdout.flush()
                time.sleep(0.2)
                #sys.stdout.write('\b')


if __name__ == '__main__':
    main()