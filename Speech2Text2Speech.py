#!/usr/bin/env python

# [START import_libraries]
from __future__ import division

import re
import sys
import time
import itertools
import os

from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types
import pyaudio
from six.moves import queue
# [END Google import_libraries]

# Hotkey functionality
import keyboard

# Colors for printing
import colorama
colorama.init()

# Initialize voice engine for tts
import pyttsx
voiceEngine = pyttsx.init()

# Set globals
voiceID = 0
playVoice = True
isListening = True
rtcRedo = False
resetPress = False
oldTime = time.time()

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
        # Check to see if our close keys have been hit, or if we need to reset for RTC
        while not self.closed and isListening and not resetPress and time.time() < oldTime + 60:
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


def listen_print_loop(responses):
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
            sys.stdout.write('> ' + transcript + overwrite_chars + '\r')
            sys.stdout.flush()

            num_chars_printed = len(transcript)

        else:
            print('> ' + transcript + overwrite_chars)
            
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
    # Check for microphone mute
    if playVoice:
        # Play the tts message using voice engine
        voiceEngine.say(ttsMessage)
        voiceEngine.runAndWait() 
    return
    
def setupHotkeys():
    # Initialize base hotkeys
    keyboard.add_hotkey('e', muteOutputTTS)
    keyboard.add_hotkey('q', closeAnalysisConnection)
    keyboard.add_hotkey('r', forceResetConnection)
    
    # Run to setup special voice hotkeys
    setupVoiceHotkeys()
    return
    
def createVoiceFile():
    # Config file isn't found, so create one
    print("No voice list file found; Creating file...")
    vfile = open("voiceListConfig.txt", "w+")
    voices = voiceEngine.getProperty('voices')
    # If 'voices' is empty, no voices are installed/found
    if len(voices) == 0:
        sys.exit("ERROR: pyttsx cannot find any installed system voices!!!")
    # Create a easy to read config file, marking off after 10 voices if needed
    for voice, number in zip(voices, range(0,len(voices))):
        if number == 10:
            vfile.write("---\n")
        vfile.write(voice.name + "\n")
    vfile.close()
    return

def readVoiceFile():
    vlist = []
    # File exists, but might be unreadble, so check
    try:
        with open("voiceListConfig.txt", "r") as vfile:
            vlist = vfile.readlines()
            #print(vlist)
        vfile.close()
    except:
        sys.exit("ERROR: Unable to read Voice List file!!!")
    
    # Create a list of names from lines in config file, cutting past 10
    for number in range(0, len(vlist)-1):
        vlist[number] = vlist[number].strip("\n")
        if vlist[number] == "---":
            vlist = vlist[:number]
            break
            
    return vlist
    
def setupVoiceHotkeys():
    # Get a list of voice names from config file
    vlist = readVoiceFile()
    voices = voiceEngine.getProperty('voices')
    vMatchList = []
    # Compare config voice list against system installed voices
    for name in vlist:
        for voice in voices:
            #print(name[:-1] + " " + voice.name)
            # If the config voice matches a system voice, add it to confirmed voice list
            if voice.name == name:
                vMatchList.append(voice)
                break

    # Create hotkeys for each confirmed voice
    print(colorama.Fore.CYAN + colorama.Style.BRIGHT + "Voice Hotkeys: " + colorama.Style.RESET_ALL)
    for number in range(0,len(vMatchList)):
        keyboard.add_hotkey(str(number), changeVoice, args=[vMatchList[number]])
        print(colorama.Fore.CYAN + colorama.Style.BRIGHT + "HotKey: " + str(number) + " - " + 
            vMatchList[number].name + colorama.Style.RESET_ALL)
    
    # Catch empty voice list
    if len(vMatchList) == 0:
        sys.exit("ERROR: No installed system voice names match names in the voiceList!!!")
    global voiceID
    voiceID = vMatchList[0].id
    
    return
        
def changeVoice(voice):
    global voiceID
    # Change voice global to indicate a voice change
    voiceID = voice.id
    print(colorama.Fore.CYAN + colorama.Style.BRIGHT + "Voice changed to: " + voice.name + colorama.Style.RESET_ALL)
    return
    
def muteOutputTTS():
    global playVoice
    # Flip Microphone check to mute/unmute
    playVoice = not playVoice
    if playVoice:
        print(colorama.Fore.GREEN)
    else:
        print(colorama.Fore.YELLOW)
    print(colorama.Style.BRIGHT + "Microphone: " + str(playVoice) + colorama.Style.RESET_ALL)
    return
    
def closeAnalysisConnection():
    global isListening
    # Flip check for a needed connection
    isListening = not isListening
    if isListening:
        print(colorama.Fore.GREEN)
    else:
        print(colorama.Fore.RED)
    print(colorama.Style.BRIGHT + "Listening: " + str(isListening) + colorama.Style.RESET_ALL)
    return
    
def forceResetConnection():
    global resetPress
    # Set a bool so connection will reset
    resetPress = True
    return

def main():
    # See http://g.co/cloud/speech/docs/languages
    # for a list of supported languages.
    language_code = 'en-US'  # a BCP-47 language tag
    
    # If a config file doesn't exist, create one
    if not os.path.isfile("voiceListConfig.txt"):
        createVoiceFile()

    # Create all hotkeys
    setupHotkeys()
    
    global oldTime, resetPress
    while(True):
        if isListening:

            oldTime = time.time()
            resetPress = False
        
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
                listen_print_loop(responses)
                
        else:
            # If we aren't connected, display an updating marker so we know we haven't crashed
            spinner = itertools.cycle(['-', '/', '|', '\\'])
            while not isListening:
                sys.stdout.write('Not Listening... ' + spinner.next() + '\r')
                sys.stdout.flush()
                time.sleep(0.2)
                oldTime = time.time()
                #sys.stdout.write('\b')


if __name__ == '__main__':
    main()