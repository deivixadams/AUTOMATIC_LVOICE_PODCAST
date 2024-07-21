import pyttsx3
import whisper
import os
import numpy as np
import librosa
import soundfile as sf
from datetime import timedelta
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips

class TextToSpeech:
    def __init__(self, text_file_path):
        self.text_file_path = text_file_path
        self.audio_file_path = "output/output_audio.wav"
        os.makedirs(os.path.dirname(self.audio_file_path), exist_ok=True)
        self.engine = pyttsx3.init()
        self.set_spanish_voice()
        self.whisper_model = whisper.load_model("base")

    def set_spanish_voice(self):
        voices = self.engine.getProperty('voices')
        for voice in voices:
            if 'spanish' in voice.name.lower():
                self.engine.setProperty('voice', voice.id)
                break
        else:
            print("No se encontró una voz en español. Asegúrate de tener una voz en español instalada.")

    def read_text(self):
        if not os.path.isfile(self.text_file_path):
            print(f"El archivo {self.text_file_path} no existe.")
            return None

        with open(self.text_file_path, "r", encoding="utf-8") as file:
            text = file.read().strip()

        if not text:
            print("El archivo de texto está vacío.")
            return None

        return text

    def convert_to_speech(self, text):
        self.engine.save_to_file(text, self.audio_file_path)
        self.engine.runAndWait()
        
        # Check if the audio file is created
        if not os.path.exists(self.audio_file_path):
            raise FileNotFoundError(f"No se pudo crear el archivo de audio en {self.audio_file_path}")
        
        return self.audio_file_path

    def apply_l_voice_effect(self, input_audio_path, output_audio_path):
        audio, sr = librosa.load(input_audio_path, sr=None)

        pitch_shift_factors = [3, -2]
        mixed_audio = np.zeros_like(audio)

        for i, pitch_shift_factor in enumerate(pitch_shift_factors):
            pitch_shifted_audio = librosa.effects.pitch_shift(audio, sr=sr, n_steps=pitch_shift_factor, bins_per_octave=12)
            original_duration = len(audio) / sr
            pitch_shifted_duration = len(pitch_shifted_audio) / sr
            stretch_factor = pitch_shifted_duration / original_duration
            stretched_audio = librosa.effects.time_stretch(pitch_shifted_audio, rate=stretch_factor)
            mixed_audio[:len(stretched_audio)] += stretched_audio

        mixed_audio[:len(audio)] += audio
        sf.write(output_audio_path, mixed_audio, sr, format='wav')

    def create_srt_word_by_word(self, audio_file_path, srt_file_path):
        result = self.whisper_model.transcribe(audio_file_path)
        with open(srt_file_path, "w", encoding="utf-8") as srt_file:
            index = 0
            for segment in result["segments"]:
                words = segment["text"].split()
                start = segment["start"]
                end = segment["end"]
                word_durations = self.calculate_word_durations(start, end, words)
                for word, (word_start, word_end) in zip(words, word_durations):
                    index += 1
                    srt_file.write(f"{index}\n")
                    srt_file.write(f"{self.format_time(word_start)} --> {self.format_time(word_end)}\n")
                    srt_file.write(f"{word}\n\n")

    def calculate_word_durations(self, start, end, words):
        total_words = len(words)
        total_duration = end - start
        adjustment_factor = 0.955
        word_duration = (total_duration / total_words) * adjustment_factor
        word_times = [(start + i * word_duration, start + (i + 1) * word_duration) for i in range(total_words)]
        return word_times

    def format_time(self, seconds):
        td = timedelta(seconds=seconds)
        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        milliseconds = td.microseconds // 1000
        return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

class ConvertirVideo:
    def __init__(self, audio_file_path, output_file_path, video_path):
        self.audio_file_path = audio_file_path
        self.video_path = video_path
        self.output_file_path = output_file_path

    def attach_audio_to_video(self):
        if not os.path.isfile(self.video_path):
            print(f"El archivo de video {self.video_path} no existe.")
            return

        if not os.path.isfile(self.audio_file_path):
            print(f"El archivo de audio {self.audio_file_path} no existe.")
            return

        video = VideoFileClip(self.video_path)
        audio = AudioFileClip(self.audio_file_path)

        video_clips = []
        current_duration = 0
        while current_duration < audio.duration:
            video_clips.append(video)
            current_duration += video.duration

        final_video = concatenate_videoclips(video_clips).set_duration(audio.duration)
        final_video = final_video.set_audio(audio)
        final_video.write_videofile(self.output_file_path, codec='libx264', audio_codec='aac')
