# SpeechToText 2 TextToSpeech
A script to convert your voice into text, and play that text back with a text-to-speech voice

## Requirements:
  * Windows
    * The keyboard capture is done using the msvcrt python library, which is Windows exclusive.
  * Python 2.7
    * Python Dependencies
      * Google Cloud
      * pyaudio
      * pyttsx
      * msvcrt
  * A Google Cloud Account


## Setup:
  * Install Python packages (Use pip)
  * Configuring your Google Cloud Speech access:
    * TBD
    
    
## Running:
  ```
  python Speech2text2Speechv3.py
  ```
  Running the script will authenticate with Google Cloud Speech.
  
  You can mute the output playing of the voice using the 'z' or 'v' keys.
  
  You can changes voices using numbers '1', '2', '3', etc.*
  
    * This is dependent on the Windows installed text-to-speech voices on your machine
  
