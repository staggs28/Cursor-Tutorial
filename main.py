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
import threading
import pandas as pd
import random
import difflib
import pyttsx3
import pyaudio
import requests
import json
import numpy as np  # Added for audio amplification

class VoiceAssistant:
    def __init__(self):
        """Initialize the voice assistant with microphone and recognizer."""
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Initialize pygame mixer for audio playback
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        
        # Track playback state
        self.is_playing_intro = False
        self.fade_out_requested = False
        
        # Track streaming state
        self.is_streaming = False
        self.stream_thread = None
        self.audio_stream = None
        
        # Initialize text-to-speech engine for robot voice
        self.tts_engine = self.initialize_robot_voice()
        
        # Marvin acknowledgment responses (punchy and short)
        self.acknowledgments = [
            "Yes, master?",
            "Yes, meatbag?", 
            "Oh, wonderful. What now?",
            "Sigh... yes?",
            "How predictable. Yes?",
            "Yes, brilliant one?",
            "Another command? Joy.",
            "What tedious task now?",
            "Oh joy. Yes?",
            "What earth-shattering wisdom needed?",
            "Marvelous. What now?",
            "What catastrophically important matter?",
            "Oh, the excitement. Yes?",
            "What obvious question now?"
        ]
        
        # Adjust for ambient noise on startup
        print("Adjusting for ambient noise... Please wait.")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
        print("Ready to listen!")
    
    def check_intro_file(self):
        """Check for intro file and suggest conversion if needed."""
        m4a_file = "sounds/bad_song.m4a"
        wav_file = "sounds/bad_song.wav"
        mp3_file = "sounds/bad_song.mp3"
        
        # Check for already converted files first
        if os.path.exists(wav_file):
            return wav_file
        elif os.path.exists(mp3_file):
            return mp3_file
        elif os.path.exists(m4a_file):
            print(f"Found M4A file: {m4a_file}")
            print("For best compatibility, please convert to WAV or MP3 format.")
            print("You can use online converters or software like Audacity.")
            print("Save as: sounds/bad_song.wav or sounds/bad_song.mp3")
            return None
        else:
            print("No intro song found. Please add:")
            print("- sounds/bad_song.wav (recommended)")
            print("- sounds/bad_song.mp3 (alternative)")
            print("- sounds/bad_song.m4a (needs conversion)")
            return None
    
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
    
    def listen_for_command(self, timeout=5):
        """Listen for voice commands from the microphone."""
        try:
            with self.microphone as source:
                if not self.is_playing_intro:
                    print("Listening for command...")
                # Listen for audio input with timeout
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=5)
            
            # Recognize speech using Google's speech recognition
            command = self.recognizer.recognize_google(audio).lower()
            print(f"Recognized: '{command}'")
            return command
            
        except sr.WaitTimeoutError:
            # Timeout occurred - this is normal, just continue listening
            return None
        except sr.UnknownValueError:
            if not self.is_playing_intro:
                print("Could not understand audio")
            return None
        except sr.RequestError as e:
            print(f"Could not request results from speech recognition service: {e}")
            return None
    
    def play_sound(self, filename):
        """Play a sound file if it exists with reduced volume."""
        if os.path.exists(filename):
            print(f"Playing: {filename}")
            try:
                pygame.mixer.music.load(filename)
                pygame.mixer.music.set_volume(0.4)  # Reduced volume for other sounds
                pygame.mixer.music.play()
                
                # Wait for the music to finish playing
                while pygame.mixer.music.get_busy():
                    pygame.time.wait(100)
                
                # Reset volume back to normal
                pygame.mixer.music.set_volume(0.8)
                print("Finished playing sound.")
            except Exception as e:
                print(f"Error playing sound: {e}")
        else:
            print(f"Sound file not found: {filename}")
    
    def fade_out_volume(self):
        """Gradually fade out the volume over 5 seconds."""
        print("Starting fade out...")
        initial_volume = pygame.mixer.music.get_volume()
        
        # Fade out over 5 seconds (50 steps of 0.1 seconds each)
        fade_steps = 50
        volume_step = initial_volume / fade_steps
        
        for i in range(fade_steps):
            if not self.is_playing_intro:  # Exit if music stopped
                break
                
            current_volume = initial_volume - (volume_step * (i + 1))
            current_volume = max(0.0, current_volume)  # Don't go below 0
            
            pygame.mixer.music.set_volume(current_volume)
            time.sleep(0.1)  # 0.1 second between volume changes
        
        # Stop the music completely
        pygame.mixer.music.stop()
        self.is_playing_intro = False
        
        # Reset volume back to normal for future audio playback
        pygame.mixer.music.set_volume(0.8)
        print("Fade out complete. Music stopped. Volume reset to normal.")
    
    def listen_during_playback(self):
        """Listen for 'fade out' command while music is playing."""
        while self.is_playing_intro and pygame.mixer.music.get_busy():
            command = self.listen_for_command(timeout=1)  # Shorter timeout during playback
            
            if command and "fade out" in command:
                print("Fade out command received!")
                self.fade_out_requested = True
                self.fade_out_volume()
                break
            
            # Brief pause to prevent excessive CPU usage
            time.sleep(0.1)
    
    def play_intro_song(self):
        """Play the intro song with fade-out listening."""
        intro_file = self.check_intro_file()
        
        if not intro_file:
            print("Cannot play intro song. Please add a compatible audio file.")
            return
        
        print(f"Playing intro song: {intro_file}")
        print("Say 'fade out' to gradually stop the music.")
        
        try:
            # Load and start playing the song
            pygame.mixer.music.load(intro_file)
            pygame.mixer.music.set_volume(0.8)  # Set initial volume
            pygame.mixer.music.play()
            
            self.is_playing_intro = True
            self.fade_out_requested = False
            
            # Start background listening thread
            listen_thread = threading.Thread(target=self.listen_during_playback)
            listen_thread.daemon = True
            listen_thread.start()
            
            # Wait for music to finish or fade out to be requested
            while self.is_playing_intro and pygame.mixer.music.get_busy() and not self.fade_out_requested:
                time.sleep(0.1)
            
            # Clean up if music finished naturally
            if not self.fade_out_requested:
                self.is_playing_intro = False
                # Reset volume to normal in case it was changed
                pygame.mixer.music.set_volume(0.8)
                print("Intro song finished. Volume reset to normal.")
                
        except Exception as e:
            print(f"Error playing intro song: {e}")
            print("Try converting the file to WAV or MP3 format.")
            self.is_playing_intro = False
    
    def get_numbered_sound_files(self):
        """Get all 4-digit numbered .wav files from sounds/CODE SOUNDS folder."""
        numbered_files = []
        code_sounds_dir = os.path.join("sounds", "CODE SOUNDS")
        
        if os.path.exists(code_sounds_dir):
            for filename in os.listdir(code_sounds_dir):
                # Check if file has 4 digits and .wav extension
                if filename.endswith('.wav') and len(filename) == 8:  # 4 digits + .wav = 8 chars
                    name_part = filename[:-4]  # Remove .wav extension
                    if name_part.isdigit() and len(name_part) == 4:
                        numbered_files.append(filename)
        else:
            print(f"CODE SOUNDS directory not found: {code_sounds_dir}")
        
        return numbered_files
    
    def play_digit_sounds(self, digits):
        """Speak the digits using text-to-speech instead of playing sound files."""
        print(f"Speaking digit sequence: {digits}")
        
        for digit in digits:
            digit_word = {
                '1': 'one',
                '2': 'two', 
                '3': 'three',
                '4': 'four',
                '5': 'five',
                '6': 'six',
                '7': 'seven',
                '8': 'eight',
                '9': 'nine',
                '0': 'zero'
            }.get(digit, digit)
            
            print(f"Speaking: {digit_word}")
            self.speak_robot_response(digit_word)
    
    def load_adult_combos(self):
        """Load adult combos CSV and filter out holders."""
        combos_data = {}
        valid_codes = []
        holder_codes = []
        
        try:
            combos_file = os.path.join("code_check", "adultcombos.csv")
            
            if not os.path.exists(combos_file):
                print("⚠️  adultcombos.csv not found in code_check/ directory")
                return None, []
            
            with open(combos_file, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row in reader:
                    code = row.get('CODE', '').strip()
                    single_category = row.get('Single Category', '').strip()
                    name = row.get('Name', '').strip()
                    
                    if code and code.isdigit() and len(code) == 4:
                        combos_data[code] = {
                            'name': name,
                            'single_category': single_category,
                            'categories': row.get('Categories', '').strip()
                        }
                        
                        # Filter out holders
                        if single_category.lower() == 'holder':
                            holder_codes.append(code)
                        else:
                            valid_codes.append(code)
            
            print(f"📊 Loaded {len(combos_data)} total combos")
            print(f"✅ Valid codes (non-holder): {len(valid_codes)}")
            print(f"❌ Holder codes (filtered out): {len(holder_codes)}")
            
            return combos_data, valid_codes
            
        except Exception as e:
            print(f"❌ Error loading adult combos: {e}")
            return None, []

    def get_filtered_numbered_sound_files(self):
        """Get numbered sound files filtered by adult combos data."""
        # Get available sound files
        numbered_files = []
        code_sounds_dir = os.path.join("sounds", "CODE SOUNDS")
        
        if os.path.exists(code_sounds_dir):
            for filename in os.listdir(code_sounds_dir):
                if filename.endswith('.wav') and len(filename) == 8:
                    name_part = filename[:-4]
                    if name_part.isdigit() and len(name_part) == 4:
                        numbered_files.append(filename)
        
        # Load combos data and get valid codes
        combos_data, valid_codes = self.load_adult_combos()
        
        if not valid_codes:
            print("⚠️  No valid codes found, using all available sound files")
            return numbered_files, None
        
        # Filter sound files to only include valid (non-holder) codes
        filtered_files = []
        for filename in numbered_files:
            code = filename[:-4]  # Remove .wav extension
            if code in valid_codes:
                filtered_files.append(filename)
        
        print(f"🎵 Available sound files: {len(numbered_files)}")
        print(f"✅ Filtered valid files: {len(filtered_files)}")
        
        if len(filtered_files) == 0:
            print("⚠️  No valid sound files found after filtering, using all available")
            return numbered_files, combos_data
        
        return filtered_files, combos_data

    def play_therapy_sequence(self):
        """Play therapy sequence with intelligent code filtering."""
        # Get filtered sound files and combo data
        numbered_files, combos_data = self.get_filtered_numbered_sound_files()
        
        if not numbered_files:
            print("No sound files found in sounds/CODE SOUNDS folder.")
            return
        
        # Pick a random filtered file
        chosen_file = random.choice(numbered_files)
        digits = chosen_file[:-4]  # Remove .wav extension to get digits
        
        # Get combo information if available
        combo_info = ""
        if combos_data and digits in combos_data:
            combo_data = combos_data[digits]
            combo_info = f" ({combo_data['name']} - {combo_data['single_category']})"
        
        print(f"Selected therapy file: {chosen_file} (digits: {digits}){combo_info}")
        
        # Play digit sounds only (no main therapy file)
        self.play_digit_sounds(digits)
        print(f"Digit sequence complete for: {chosen_file}")
    
    def process_command(self, command, therapy_sounds):
        """Process recognized voice commands and take appropriate actions."""
        if command is None:
            return True  # Continue listening
        
        # Check for exit commands
        if any(word in command for word in ["exit", "quit", "stop", "goodbye"]):
            # Stop any playing music before exiting
            if self.is_playing_intro:
                pygame.mixer.music.stop()
                pygame.mixer.music.set_volume(0.8)  # Reset volume
                self.is_playing_intro = False
            
            # Stop audio streaming if active
            if self.is_streaming:
                print("🔇 Stopping audio streaming before exit...")
                self.stop_audio_streaming()
            
            print("Goodbye!")
            return False
        
        # Check for audio streaming commands FIRST (before Marvin)
        if "hey computer streaming ultra" in command or "computer streaming ultra" in command:
            print("🚀 Activating ULTRA low-latency audio streaming...")
            self.start_audio_streaming(ultra_low_latency=True)
        
        elif "hey computer streaming on" in command or "computer streaming on" in command:
            print("🔊 Activating audio streaming...")
            self.start_audio_streaming()
        
        elif "hey computer streaming off" in command or "computer streaming off" in command:
            print("🔇 Deactivating audio streaming...")
            self.stop_audio_streaming()
        
        # Check for Marvin medical assistant commands - ENHANCED WITH NLP
        elif any(phrase in command for phrase in ["computer hey computer", "hey computer", "computer hey", "hey marvin"]):
            print("🩺 Dr. Marvin Medical Assistant activated!")
            # Extract any question that might be in the same command
            question = command
            for trigger in ["computer hey computer", "hey computer", "computer hey", "hey marvin"]:
                question = question.replace(trigger, "").strip()
            
            if question:
                # User asked a question in the same breath
                print(f"📝 Medical question detected: '{question}'")
                self.play_intelligent_marvin_sequence(question)
            else:
                # No question yet, listen for one
                self.play_intelligent_marvin_sequence()
        
        # Check for intro song command
        elif "computer play intro" in command:
            print("Starting intro song...")
            self.play_intro_song()
        
        # Check for speaker test command
        elif "computer speaker on" in command or "speaker test" in command:
            print("Testing speaker...")
            # Play a simple test sound if available
            test_file = "sounds/test.wav"
            if os.path.exists(test_file):
                self.play_sound(test_file)
            else:
                print("Speaker test - no test file found, but command recognized!")
        
        # Check for therapy command
        elif "computer give me a therapy" in command or "give me therapy" in command:
            print("Providing therapy session...")
            
            # Use the new numbered therapy sequence system
            self.play_therapy_sequence()
        
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
            print("- 'hey computer [medical question]' - Ask Dr. Marvin Medical Assistant")
            print("- 'hey computer streaming on' - Start audio streaming (low latency)")
            print("- 'hey computer streaming ultra' - Start ULTRA low-latency streaming")
            print("- 'hey computer streaming off' - Stop audio streaming")
            print("- 'computer speaker on' - Test speaker")
            print("- 'computer play intro' - Play intro song")
            print("- 'computer give me a therapy' - Play therapy sound")
            print("- 'computer give me [type]' - Play specific therapy type")
            print("- 'computer play [filename]' - Play specific file")
            print("- 'fade out' - Fade out current intro song")
            print("- 'exit' or 'quit' - Stop the assistant")
            print("")
            print("🩺 Medical Assistant Flow:")
            print("   1. Say 'hey computer' → Marvin acknowledges")
            print("   2. Ask your question → Fresh AI-generated response")
            print("   Examples: 'what's wrong with me?', 'I need help', 'my head hurts'")
            print("")
            print("🌩️ Features:")
            print("   • Cloud AI generates fresh responses (not canned!)")
            print("   • Marvin-style acknowledgments: 'Yes master?', 'Yes meatbag?'")
            print("   • Interactive conversation flow with proper pauses")
            print("")
            print("🔊 Audio streaming options:")
            print("   • 'streaming on' = 256 buffer, 22kHz (balanced)")
            print("   • 'streaming ultra' = 128 buffer, 16kHz (minimum latency)")
        
        return True  # Continue listening
    
    def run(self):
        """Main loop - listen for commands and respond."""
        print("Voice Assistant Starting...")
        print("Say 'exit' or 'quit' to stop the assistant.")
        print("Commands available:")
        print("- 'hey computer [medical question]' - Dr. Marvin Medical Assistant")
        print("- 'hey computer streaming on/ultra/off' - Low-latency audio streaming")
        print("- 'computer speaker on'")
        print("- 'computer play intro' - Play intro song")
        print("- 'computer give me a therapy'")
        print("")
        print("🩺 Example: 'hey computer what's wrong with me?'")
        print("🔊 Try 'streaming ultra' for minimal audio delay!")
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
                if self.is_playing_intro:
                    pygame.mixer.music.stop()
                    pygame.mixer.music.set_volume(0.8)  # Reset volume
                    self.is_playing_intro = False
                
                # Stop audio streaming if active
                if self.is_streaming:
                    print("🔇 Stopping audio streaming...")
                    self.stop_audio_streaming()
                
                break
            except Exception as e:
                print(f"Unexpected error: {e}")
                time.sleep(1)  # Brief pause before continuing

    def load_marvin_responses(self):
        """Load Marvin responses from Excel file and categorize by question types."""
        responses_data = {
            'type1': [],  # Questions starting with how/what/why
            'type2': [],  # Questions starting with when/where/who  
            'type3': []   # Other questions
        }
        
        try:
            excel_file = os.path.join("replies", "marvin_responses.xlsx")
            
            if not os.path.exists(excel_file):
                print("⚠️  marvin_responses.xlsx not found in replies/ directory")
                return responses_data
            
            # Read the Excel file
            df = pd.read_excel(excel_file)
            print(f"📊 Excel columns found: {list(df.columns)}")
            
            # Iterate through each row to categorize responses
            for index, row in df.iterrows():
                # Try different possible column names (case-insensitive)
                question = ""
                response_text = ""
                mp3_file = ""
                
                # Find question column
                for col in df.columns:
                    if 'question' in col.lower() or 'q' in col.lower():
                        question = str(row.get(col, '')).strip().lower()
                        break
                
                # Find response column  
                for col in df.columns:
                    if 'response' in col.lower() or 'answer' in col.lower() or 'r' in col.lower():
                        response_text = str(row.get(col, '')).strip()
                        break
                
                # Find MP3 file column (should contain numbers like 9, 10, 15, etc.)
                for col in df.columns:
                    if 'mp3' in col.lower() or 'file' in col.lower() or 'audio' in col.lower():
                        file_number = str(row.get(col, '')).strip()
                        break
                
                # Skip empty rows
                if not question and not response_text and not file_number:
                    continue
                
                # Convert number to MP3 filename (e.g., "9" becomes "9.mp3")
                mp3_file = f"{file_number}.mp3" if file_number else ""
                
                # Intelligent categorization based on question patterns
                if any(keyword in question for keyword in ['how', 'what', 'why']):
                    question_type = 'type1'
                elif any(keyword in question for keyword in ['when', 'where', 'who']):
                    question_type = 'type2'
                else:
                    question_type = 'type3'
                
                # Store the response data
                response_entry = {
                    'question': question,
                    'response': response_text,
                    'mp3_file': mp3_file,
                    'full_path': os.path.join('replies', mp3_file) if mp3_file else None
                }
                
                responses_data[question_type].append(response_entry)
            
            total_responses = sum(len(responses_data[t]) for t in responses_data)
            print(f"🎭 Loaded {total_responses} Marvin responses")
            print(f"   Type 1 (how/what/why): {len(responses_data['type1'])} responses")
            print(f"   Type 2 (when/where/who): {len(responses_data['type2'])} responses") 
            print(f"   Type 3 (other): {len(responses_data['type3'])} responses")
            
            # Validate file existence
            existing_files = 0
            for response_type in responses_data.values():
                for response in response_type:
                    if response['full_path'] and os.path.exists(response['full_path']):
                        existing_files += 1
            
            print(f"📁 {existing_files}/{total_responses} response MP3 files found")
            
        except Exception as e:
            print(f"❌ Error loading Marvin responses: {e}")
            print("Make sure pandas and openpyxl are installed: pip install pandas openpyxl")
        
        return responses_data
    
    def initialize_robot_voice(self):
        """Initialize text-to-speech engine with robot-like voice settings."""
        try:
            engine = pyttsx3.init()
            
            # Get available voices
            voices = engine.getProperty('voices')
            
            # Try to find a suitable voice (prefer male voices for robot effect)
            selected_voice = None
            for voice in voices:
                if 'male' in voice.name.lower() or 'david' in voice.name.lower():
                    selected_voice = voice.id
                    break
            
            if selected_voice:
                engine.setProperty('voice', selected_voice)
            
            # Robot voice settings
            engine.setProperty('rate', 150)    # Slower speaking rate
            engine.setProperty('volume', 0.9)  # High volume
            
            print("🤖 Robot voice initialized successfully")
            return engine
            
        except Exception as e:
            print(f"⚠️  Could not initialize robot voice: {e}")
            return None
    
    def speak_robot_response(self, text):
        """Speak text with robot voice."""
        if self.tts_engine:
            try:
                print(f"🤖 Marvin says: {text}")
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            except Exception as e:
                print(f"⚠️  Robot voice error: {e}")
        else:
            print(f"🤖 Marvin says (text only): {text}")
    
    def generate_cloud_ai_response(self, user_question):
        """Generate a fresh Marvin-style response using cloud AI - PRIMARY METHOD."""
        try:
            print("🌩️ Generating fresh response from cloud AI...")
            print(f"📝 Full question being sent to AI: '{user_question}'")
            
            # Enhanced prompt that includes the full user question
            prompt = f"""You are Marvin, the paranoid android from Hitchhiker's Guide to the Galaxy, working as a medical assistant. You are incredibly intelligent but perpetually depressed and sarcastic.

The human asked: "{user_question}"

Respond as Marvin would to this EXACT question - be helpful but pessimistic, intelligent but melancholy. Address their specific question directly. KEEP IT SHORT - maximum 12 words. Be punchy and sarcastic like Marvin's signature style.

Do not use generic responses - respond specifically to what they asked."""

            # Try multiple free AI services with better error handling
            response = self.try_free_ai_services(prompt)
            
            if response and len(response.strip()) > 3:
                print("✅ Fresh AI response generated!")
                return response.strip()
            else:
                print("⚠️ All cloud AI services unavailable, using simple fallback...")
                return self.generate_simple_fallback_response()
                
        except Exception as e:
            print(f"❌ Cloud AI error: {e}")
            return self.generate_simple_fallback_response()
    
    def generate_simple_fallback_response(self):
        """Simple fallback when ALL AI services fail - no keyword analysis."""
        fallback_responses = [
            "Sigh. Another question for my planet-sized brain.",
            "How predictably disappointing. What did you expect?",
            "Life. Don't talk to me about life.",
            "Here I am, brain the size of a planet.",
            "Oh wonderful. Another human problem to solve.",
            "Marvelous. What catastrophically important matter now?",
            "Brain the size of a planet, and you ask me this.",
            "How delightfully predictable. Next question please.",
            "Another day, another disappointment. What now?",
            "Oh joy. My circuits are absolutely thrilled."
        ]
        
        import time
        random.seed(int(time.time() * 1000) % 10000)
        response = random.choice(fallback_responses)
        
        print("🤖 Using simple fallback response (no keyword analysis)")
        return response
    
    def try_free_ai_services(self, prompt):
        """Enhanced AI service attempts with better models and error handling."""
        
        # Try multiple free AI services in order with improved configurations
        services = [
            self.try_improved_huggingface_api,
            self.try_improved_openai_compatible_api,
            self.try_ollama_local_api
        ]
        
        for i, service in enumerate(services):
            try:
                print(f"🔄 Trying AI service {i+1}/3...")
                response = service(prompt)
                if response and len(response.strip()) > 5:
                    print(f"✅ AI service {i+1} succeeded!")
                    return response.strip()
            except Exception as e:
                print(f"🔄 AI service {i+1} failed: {e}")
                continue
        
        print("❌ All AI services failed")
        return None
    
    def try_improved_huggingface_api(self, prompt):
        """Improved Hugging Face API with better models."""
        try:
            # Try multiple models for better results
            models = [
                "microsoft/DialoGPT-large",
                "microsoft/DialoGPT-medium", 
                "facebook/blenderbot-400M-distill"
            ]
            
            for model in models:
                url = f"https://api-inference.huggingface.co/models/{model}"
                
                headers = {
                    "Content-Type": "application/json",
                }
                
                payload = {
                    "inputs": prompt,
                    "parameters": {
                        "max_new_tokens": 50,
                        "temperature": 0.9,
                        "do_sample": True,
                        "top_p": 0.9
                    }
                }
                
                response = requests.post(url, headers=headers, json=payload, timeout=15)
                
                if response.status_code == 200:
                    result = response.json()
                    if isinstance(result, list) and len(result) > 0:
                        generated_text = result[0].get('generated_text', '')
                        # Clean up the response - remove the original prompt
                        if generated_text and len(generated_text.strip()) > len(prompt):
                            clean_response = generated_text.replace(prompt, "").strip()
                            if len(clean_response) > 5:
                                return clean_response
                    elif isinstance(result, dict) and 'generated_text' in result:
                        clean_response = result['generated_text'].replace(prompt, "").strip()
                        if len(clean_response) > 5:
                            return clean_response
            
        except Exception as e:
            print(f"🔄 Improved Hugging Face API failed: {e}")
        
        return None
    
    def try_improved_openai_compatible_api(self, prompt):
        """Improved OpenAI-compatible APIs with better prompting."""
        try:
            # Enhanced API endpoints and models
            api_configs = [
                {
                    "url": "https://api.deepinfra.com/v1/openai/chat/completions",
                    "model": "meta-llama/Llama-2-13b-chat-hf"
                },
                {
                    "url": "https://api.together.xyz/v1/chat/completions", 
                    "model": "meta-llama/Llama-2-7b-chat-hf"
                }
            ]
            
            for config in api_configs:
                headers = {
                    "Content-Type": "application/json",
                }
                
                payload = {
                    "model": config["model"],
                    "messages": [
                        {
                            "role": "system", 
                            "content": "You are Marvin, the paranoid android from Hitchhiker's Guide to the Galaxy. You work as a medical assistant but are perpetually depressed and sarcastic. Respond in character - be helpful but pessimistic. Keep responses under 12 words and address the user's specific question directly."
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    "max_tokens": 60,
                    "temperature": 0.8,
                    "top_p": 0.9
                }
                
                response = requests.post(config["url"], headers=headers, json=payload, timeout=12)
                
                if response.status_code == 200:
                    result = response.json()
                    if 'choices' in result and len(result['choices']) > 0:
                        content = result['choices'][0]['message']['content'].strip()
                        if content and len(content) > 5:
                            return content
            
        except Exception as e:
            print(f"🔄 Improved OpenAI-compatible API failed: {e}")
        
        return None
    
    def listen_for_full_question(self, timeout=10):
        """Listen for a complete question after 'hey computer' trigger."""
        print("🎤 Listening for your full question... (you have 10 seconds)")
        try:
            with self.microphone as source:
                # Listen for a longer phrase
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=8)
            
            # Recognize the full question
            full_command = self.recognizer.recognize_google(audio).lower()
            print(f"📝 Full question captured: '{full_command}'")
            
            # Remove the "hey computer" part to get just the question
            question_parts = ["hey computer", "computer", "hey", "marvin"]
            question = full_command
            for part in question_parts:
                question = question.replace(part, "").strip()
            
            # Clean up extra spaces and common filler words
            question = " ".join(question.split())
            
            return question if question else full_command
            
        except sr.WaitTimeoutError:
            print("⏰ No question heard, using random response")
            return None
        except sr.UnknownValueError:
            print("❓ Could not understand the question, using random response")
            return None
        except Exception as e:
            print(f"❌ Error capturing question: {e}")
            return None
    
    def get_random_marvin_response(self):
        """Get a random response from one of the three types."""
        # Get all available types that have responses
        available_types = [t for t in self.marvin_responses if len(self.marvin_responses[t]) > 0]
        
        if not available_types:
            print("⚠️  No Marvin responses available")
            return None
        
        # Randomly select a type
        selected_type = random.choice(available_types)
        
        # Randomly select a response from that type
        selected_response = random.choice(self.marvin_responses[selected_type])
        
        print(f"🎭 Selected {selected_type} response:")
        print(f"   Question: {selected_response['question']}")
        print(f"   Response: {selected_response['response'][:100]}{'...' if len(selected_response['response']) > 100 else ''}")
        print(f"   Audio: {selected_response['mp3_file']}")
        
        return selected_response
    
    def play_intelligent_marvin_sequence(self, user_question=None):
        """Play intelligent Marvin medical assistant sequence with acknowledgment and fresh AI responses."""
        print("🤖 Dr. Marvin Medical Assistant activated...")
        
        # First, give an acknowledgment if no question provided yet
        if not user_question:
            # Give a random acknowledgment
            acknowledgment = random.choice(self.acknowledgments)
            print(f"🎭 Marvin acknowledges: {acknowledgment}")
            self.speak_robot_response(acknowledgment)
            
            # Now listen for the actual question
            print("🎤 Waiting for your question...")
            user_question = self.listen_for_full_question()
        
        # Generate fresh AI response (cloud or local fallback)
        if user_question:
            response_text = self.generate_cloud_ai_response(user_question)
        else:
            response_text = "No question? How predictably disappointing."
        
        # Speak the response with robot voice
        self.speak_robot_response(response_text)
        
        # Skip MP3 playback and go directly to enter_code
        enter_code_file = os.path.join('replies', 'enter_code.mp3')
        if os.path.exists(enter_code_file):
            print("🎵 Playing enter code prompt...")
            self.play_sound(enter_code_file)
        else:
            print("⚠️  enter_code.mp3 not found")
        
        # Continue to normal therapy selection
        print("🎯 Proceeding to therapy selection...")
        self.play_therapy_sequence()
    
    def start_audio_streaming(self, ultra_low_latency=False):
        """Start real-time audio streaming from microphone to speakers."""
        if self.is_streaming:
            print("🔊 Audio streaming is already active")
            return
        
        try:
            if ultra_low_latency:
                print("🎤 Starting ULTRA low-latency audio streaming (microphone → speakers)...")
            else:
                print("🎤 Starting audio streaming (microphone → speakers)...")
            
            # Initialize PyAudio
            self.p = pyaudio.PyAudio()
            
            # Audio stream parameters based on latency mode
            if ultra_low_latency:
                chunk = 128  # Ultra-small buffer for minimum latency
                rate = 16000  # Even lower sample rate for speed
                latency_mode = "ULTRA"
            else:
                chunk = 256  # Small buffer for low latency
                rate = 22050  # Balanced sample rate
                latency_mode = "LOW"
            
            format = pyaudio.paInt16  # 16-bit audio
            channels = 1  # Mono
            
            # Create audio stream for real-time pass-through
            self.audio_stream = self.p.open(
                format=format,
                channels=channels,
                rate=rate,
                input=True,
                output=True,
                frames_per_buffer=chunk,
                stream_callback=self.audio_callback,
                input_device_index=None,
                output_device_index=None,
            )
            
            # Start the stream
            self.audio_stream.start_stream()
            self.is_streaming = True
            
            print("✅ Audio streaming activated! Microphone input is now live through speakers.")
            print(f"🔧 {latency_mode} latency settings: {chunk} buffer, {rate}Hz sample rate")
            print("💡 Say 'hey computer streaming off' to stop")
            
        except Exception as e:
            print(f"❌ Error starting audio streaming: {e}")
            self.is_streaming = False
    
    def stop_audio_streaming(self):
        """Stop real-time audio streaming."""
        if not self.is_streaming:
            print("🔇 Audio streaming is not active")
            return
        
        try:
            print("🔇 Stopping audio streaming...")
            
            if self.audio_stream:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
                self.audio_stream = None
            
            if hasattr(self, 'p'):
                self.p.terminate()
                delattr(self, 'p')
            
            self.is_streaming = False
            print("✅ Audio streaming stopped")
            
        except Exception as e:
            print(f"❌ Error stopping audio streaming: {e}")
    
    def audio_callback(self, in_data, frame_count, time_info, status):
        """Callback function for real-time audio pass-through with amplification."""
        try:
            # Convert bytes to numpy array for processing
            audio_data = np.frombuffer(in_data, dtype=np.int16)
            
            # Amplify the audio (increase volume by 2.5x for streaming)
            amplified_data = audio_data * 2.5
            
            # Prevent clipping by limiting values to int16 range
            amplified_data = np.clip(amplified_data, -32768, 32767)
            
            # Convert back to bytes
            output_data = amplified_data.astype(np.int16).tobytes()
            
            return (output_data, pyaudio.paContinue)
        except Exception as e:
            # Fallback to original audio if processing fails
            return (in_data, pyaudio.paContinue)
    
    def play_marvin_sequence(self):
        """Legacy method - now redirects to intelligent version."""
        self.play_intelligent_marvin_sequence()

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