#!/usr/bin/env python3
"""
Voice-Controlled Desktop Assistant for Windows
A simple assistant that listens for voice commands and responds with audio.
"""

import speech_recognition as sr
import csv
import os
import sys
import pygame
import time

class VoiceAssistant:
    def __init__(self):
        """Initialize the voice assistant with microphone and recognizer."""
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Initialize pygame mixer for audio playback
        pygame.mixer.init()
        
        # Adjust for ambient noise on startup
        print("Adjusting for ambient noise... Please wait.")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
        print("Ready to listen!")
    
    def load_therapy_sounds(self):
        """Load therapy sounds from CSV file into a dictionary."""
        therapy_sounds = {}
        csv_file = "therapies.csv"
        
        if not os.path.exists(csv_file):
            print(f"Warning: {csv_file} not found. Creating sample file.")
            self.create_sample_csv()
        
        try:
            with open(csv_file, 'r', newline='') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    therapy_sounds[row['type'].lower()] = row['filename']
            print(f"Loaded {len(therapy_sounds)} therapy sounds from CSV.")
        except Exception as e:
            print(f"Error loading therapy sounds: {e}")
        
        return therapy_sounds
    
    def create_sample_csv(self):
        """Create a sample therapies.csv file with example entries."""
        sample_data = [
            {'type': 'calm', 'filename': 'sounds/calm1.mp3'},
            {'type': 'funny', 'filename': 'sounds/funny1.mp3'},
            {'type': 'meditation', 'filename': 'sounds/meditation1.mp3'},
            {'type': 'nature', 'filename': 'sounds/nature1.mp3'}
        ]
        
        with open('therapies.csv', 'w', newline='') as file:
            fieldnames = ['type', 'filename']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(sample_data)
        print("Created sample therapies.csv file.")
    
    def listen_for_command(self):
        """Listen for voice commands from the microphone."""
        try:
            with self.microphone as source:
                print("Listening for command...")
                # Listen for audio input with timeout
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
            
            # Recognize speech using Google's speech recognition
            command = self.recognizer.recognize_google(audio).lower()
            print(f"Recognized: '{command}'")
            return command
            
        except sr.WaitTimeoutError:
            # Timeout occurred - this is normal, just continue listening
            return None
        except sr.UnknownValueError:
            print("Could not understand audio")
            return None
        except sr.RequestError as e:
            print(f"Could not request results from speech recognition service: {e}")
            return None
    
    def play_sound(self, filename):
        """Play a sound file if it exists."""
        if os.path.exists(filename):
            print(f"Playing: {filename}")
            try:
                pygame.mixer.music.load(filename)
                pygame.mixer.music.play()
                
                # Wait for the music to finish playing
                while pygame.mixer.music.get_busy():
                    pygame.time.wait(100)
                
                print("Finished playing sound.")
            except Exception as e:
                print(f"Error playing sound: {e}")
        else:
            print(f"Sound file not found: {filename}")
    
    def process_command(self, command, therapy_sounds):
        """Process recognized voice commands and take appropriate actions."""
        if command is None:
            return True  # Continue listening
        
        # Check for exit commands
        if any(word in command for word in ["exit", "quit", "stop", "goodbye"]):
            print("Goodbye!")
            return False
        
        # Check for speaker test command
        if "computer speaker on" in command or "speaker test" in command:
            print("Testing speaker...")
            # Play a simple test sound if available
            test_file = "sounds/test.mp3"
            if os.path.exists(test_file):
                self.play_sound(test_file)
            else:
                print("Speaker test - no test file found, but command recognized!")
        
        # Check for therapy command
        elif "computer give me a therapy" in command or "give me therapy" in command:
            print("Providing therapy session...")
            
            # Look for a default therapy sound or the first available one
            if therapy_sounds:
                # Try to find a 'calm' therapy first, otherwise use the first available
                therapy_type = 'calm' if 'calm' in therapy_sounds else list(therapy_sounds.keys())[0]
                self.play_sound(therapy_sounds[therapy_type])
            else:
                print("No therapy sounds available. Please add sound files to the sounds/ folder.")
        
           # Check for specific therapy type requests
        elif "computer give me" in command:
            # Extract therapy type from command
            words = command.split()
            if "give" in words and "me" in words:
                try:
                    give_index = words.index("give")
                    me_index = words.index("me")
                    if me_index == give_index + 1 and len(words) > me_index + 1:
                        therapy_type = words[me_index + 1].lower()
                        if therapy_type in therapy_sounds:
                            print(f"Playing {therapy_type} therapy...")
                            self.play_sound(therapy_sounds[therapy_type])
                        else:
                            print(f"Therapy type '{therapy_type}' not found.")
                            print(f"Available types: {list(therapy_sounds.keys())}")
                except (ValueError, IndexError):
                    print("Could not understand therapy request.")
        
        # Check for direct file play command
        elif "computer play" in command:
            words = command.split()
            if "play" in words:
                try:
                    play_index = words.index("play")
                    if len(words) > play_index + 1:
                        filename = words[play_index + 1]
                        # Add .mp3 extension if not present
                        if not filename.endswith('.mp3'):
                            filename += '.mp3'
                        # Check in sounds folder
                        full_path = os.path.join('sounds', filename)
                        self.play_sound(full_path)
                except (ValueError, IndexError):
                    print("Could not understand file play request.")
        
        else:
            print(f"Command not recognized: '{command}'")
            print("Available commands:")
            print("- 'computer speaker on' - Test speaker")
            print("- 'computer give me a therapy' - Play therapy sound")
            print("- 'computer give me [type]' - Play specific therapy type")
            print("- 'computer play [filename]' - Play specific file")
            print("- 'exit' or 'quit' - Stop the assistant")
        
        return True  # Continue listening
    
    def run(self):
        """Main loop - listen for commands and respond."""
        print("Voice Assistant Starting...")
        print("Say 'exit' or 'quit' to stop the assistant.")
        print("Commands available:")
        print("- 'computer speaker on'")
        print("- 'computer give me a therapy'")
        print("-" * 50)
        
        # Load therapy sounds from CSV
        therapy_sounds = self.load_therapy_sounds()
        
        # Main listening loop
        while True:
            try:
                command = self.listen_for_command()
                if not self.process_command(command, therapy_sounds):
                    break  # Exit command received
            except KeyboardInterrupt:
                print("\nStopping assistant...")
                break
            except Exception as e:
                print(f"Unexpected error: {e}")
                time.sleep(1)  # Brief pause before continuing

def main():
    """Main function to start the voice assistant."""
    # Check if required directories exist
    if not os.path.exists('sounds'):
        os.makedirs('sounds')
        print("Created 'sounds' directory. Please add your sound files here.")
    
    # Create and run the assistant
    assistant = VoiceAssistant()
    assistant.run()

if __name__ == "__main__":
    main() 