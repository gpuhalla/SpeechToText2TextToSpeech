# SpeechToText 2 TextToSpeech
A script to convert your voice into text, and play that text back with a text-to-speech voice

## Requirements:
  * **NOTE:** Only tested on Windows, but should work on other OS's
  * Python 2.7
    * Python Dependencies
      * Google Cloud (google-cloud)
      * pyaudio
      * pyttsx
      * keyboard
      * colorama
  * A Google Cloud Account

## Install:
  * Install Python packages (Use pip with the names above)

## Setup:
  * Configuring your Google Cloud Speech access:
    * TBD
       
## Running:
  ```
  python Speech2text2Speech.py
  ```
  Running the script will authenticate with Google Cloud Speech.
  
  The first time you run the script, it will create a _voiceList.txt_ file in the same directory of the script. This file will be populated by the voices installed on the machine. The voices will be assigned to the numbered keys as Hotkeys for the voice in the order that they are listed. If the voice count is > 10, then there will be a marker "---" to denote that any voices below said marker will not be bound to hotkeys. You can edit this file to reorder the voices any way you wish by cutting and pasting each name, as long as you follow the following:
  * There are no more than 10 voices before the "---" marker
  * The voices always match their system "name"
    
  You can therefore change voices using numbers '0', '1', '2', '3', etc.
  * This is dependent on the number of installed text-to-speech voices on your machine. These hotkeys are printed onscreen at the start of running the script.
  
  You can mute the output playing of the voice using the 'E' key.
  
  You can close your connection to the Google Cloud Speech using the 'Q' key.
  * This will allow you to save speech analysis time by disconnecting when you aren't speaking, as well as avoid RPC timeouts when not speaking for long periods of time.
  
  You can manually reset your connection to avoid RPC timeouts by pressing the 'R' key.
  * I'm working to find a better way to deal with the timeout issue

  
## Output:
  If you want to use the speech playback of the text as your voice in an application, you will need to redirect the audio from your output device back to an input device. To do this, I recommend using [Virtual Audio Cables](https://www.vb-audio.com/Cable/index.htm#DownloadCable) along with [Audio Router](https://github.com/audiorouterdev/audio-router) for better sound management.
  
## More Voices - Windows:
  Since I took forever to find something that could do it, I have add a powershell script to the repo that will add the Microsoft OneCore voices to the available voices in Windows. These voices can be added to by downloading the speech pack for the Windows 10 languages. To have the script successfully execute, you must run it in administrator mode.
  
## License + References:
 Since the main script is based heavily on the Google Cloud Speech streaming example [here](https://cloud.google.com/speech/docs/streaming-recognize) , I have copied the license they used.
 
 The Powershell script for the additional Windows voices is taken from Reddit user _Pessimist__Prime_ [here](https://www.reddit.com/r/EliteDangerous/comments/5d02vv/if_you_use_voiceattack_eddi_or_any_other/?st=jcy6yvq9&sh=fc13dc2e)
