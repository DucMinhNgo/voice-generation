from pydub import AudioSegment

# Load the two 14-second MP3 files
audio1 = AudioSegment.from_mp3("output.mp3")
audio2 = AudioSegment.from_mp3("output2.mp3")

# Ensure both audio segments are 14 seconds long
target_duration = 14 * 1000  # 14 seconds in milliseconds
audio1 = audio1[:target_duration]
audio2 = audio2[:target_duration]

# Mix the two audio segments
mixed_audio = audio1.overlay(audio2)

# Export the mixed audio as an MP3 file
mixed_audio.export("mixed.mp3", format="mp3")

print("Mixing completed.")
