# Voice-Controlled Desktop Assistant

A simple voice-controlled desktop assistant for Windows that listens to spoken commands and responds by playing audio files.

## Features

- **Continuous Voice Listening**: Always listening for voice commands
- **Speech Recognition**: Recognizes specific spoken commands
- **Audio Playback**: Plays MP3 files through your default speaker
- **Therapy Sound Management**: Uses CSV file to organize therapy sounds by category
- **Beginner-Friendly**: Clear, commented code that's easy to understand and modify

## Supported Commands

- `"computer speaker on"` - Test your speakers
- `"computer give me a therapy"` - Play a therapy sound (defaults to calm)
- `"computer give me [type]"` - Play specific therapy type (calm, funny, meditation, etc.)
- `"computer play [filename]"` - Play a specific file from the sounds folder
- `"exit"` or `"quit"` - Stop the assistant

## Installation

### Prerequisites

- Python 3.7 or higher
- A working microphone
- Internet connection (for Google Speech Recognition)

### Setup Steps

1. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Create Sounds Directory**:
   The program will automatically create a `sounds/` folder when first run, but you can create it manually:
   ```bash
   mkdir sounds
   ```

3. **Add Your Sound Files**:
   - Place your MP3 files in the `sounds/` folder
   - Update `therapies.csv` to match your sound files
   - Supported formats: MP3 (recommended), WAV

### Windows-Specific Setup

If you encounter issues with PyAudio on Windows:

1. **Install PyAudio using conda** (if you have Anaconda/Miniconda):
   ```bash
   conda install pyaudio
   ```

2. **Or download the wheel file**:
   - Visit: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
   - Download the appropriate `.whl` file for your Python version
   - Install with: `pip install downloaded_file.whl`

## Usage

1. **Start the Assistant**:
   ```bash
   python main.py
   ```

2. **Wait for Initialization**:
   The program will adjust for ambient noise and display "Ready to listen!"

3. **Speak Commands**:
   Speak clearly and wait for the "Listening for command..." prompt

4. **Stop the Assistant**:
   Say "exit" or "quit", or press Ctrl+C

## File Structure

```
voice-assistant/
├── main.py              # Main program file
├── therapies.csv        # Therapy sounds database
├── requirements.txt     # Python dependencies
├── README.md           # This file
└── sounds/             # Directory for audio files
    ├── calm1.mp3
    ├── funny1.mp3
    ├── meditation1.mp3
    └── ...
```

## Customization

### Adding New Therapy Types

1. **Add audio files** to the `sounds/` folder
2. **Update therapies.csv**:
   ```csv
   type,filename
   calm,sounds/calm1.mp3
   energetic,sounds/energetic1.mp3
   ```

### Modifying Commands

Edit the `process_command()` method in `main.py` to add new voice commands or change existing ones.

## Troubleshooting

### Common Issues

1. **"No module named 'speech_recognition'"**:
   - Install dependencies: `pip install -r requirements.txt`

2. **Microphone not working**:
   - Check Windows microphone permissions
   - Ensure microphone is set as default recording device

3. **Internet connection required**:
   - The assistant uses Google's speech recognition service
   - Ensure stable internet connection

4. **Audio playback issues**:
   - Verify audio files are in MP3 format
   - Check Windows audio settings
   - Ensure speakers/headphones are connected

### Windows Audio Setup

1. **Set Default Playback Device**:
   - Right-click speaker icon in system tray
   - Select "Playback devices"
   - Set your preferred device as default

2. **Microphone Permissions**:
   - Windows Settings > Privacy > Microphone
   - Allow apps to access microphone

## Stretch Goals (Future Enhancements)

- [ ] Bluetooth speaker support
- [ ] Text-to-speech responses using pyttsx3
- [ ] Custom wake word detection
- [ ] GUI interface
- [ ] Voice training for better recognition
- [ ] Local speech recognition (offline mode)

## Technical Details

- **Speech Recognition**: Uses Google Speech Recognition API
- **Audio Playback**: Uses playsound library for cross-platform audio
- **CSV Management**: Built-in csv module for therapy sound database
- **Error Handling**: Comprehensive exception handling for robust operation

## Contributing

This project is designed to be beginner-friendly. Feel free to:
- Add new voice commands
- Improve speech recognition accuracy
- Add new audio file formats
- Enhance error handling

## License

This project is provided as-is for educational purposes. Modify and use as needed for your personal projects. 