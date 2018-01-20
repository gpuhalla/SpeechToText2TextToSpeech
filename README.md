# SpeechToText 2 TextToSpeech
A script to convert your voice into text, and play that text back with a text-to-speech voice

## Requirements:
  * Windows
    * The keyboard capture is done using the msvcrt python library, which is Windows exclusive.
  * Python 2.7
    * Python Dependencies
      * Google Cloud (google-cloud)
      * pyaudio
      * pyttsx
      * msvcrt
      * colorama
  * A Google Cloud Account

## Install:
  * Install Python packages (Use pip with the names above)


## Setup:
  * Configuring your Google Cloud Speech access:
    * TBD
    
    
## Running:
  ```
  python Speech2text2Speechv3.py
  ```
  Running the script will authenticate with Google Cloud Speech.
  
  You can mute the output playing of the voice using the 'z' key.
  
  You can changes voices using numbers '1', '2', '3', etc.
  * This is dependent on the Windows installed text-to-speech voices on your machine
  
## Output
  If you want to use the speech playback of the text as your voice in an application, you will need to redirect the audio from you output device back to an input device. To do this, I recommend using [Virtual Audio Cables](https://www.vb-audio.com/Cable/index.htm#DownloadCable) along with [Audio Router](https://github.com/audiorouterdev/audio-router) for better sound management.
  
## License:
 Since this is based heavily on the Google Cloud Speech streaming example [here](https://cloud.google.com/speech/docs/streaming-recognize) , I have copied the license they used.
