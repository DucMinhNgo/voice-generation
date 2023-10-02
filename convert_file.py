from scipy.io.wavfile import write as write_wav
from pydub import AudioSegment

filename = "0cad4139-5255-400d-a65c-43f11dc7d1c1"
wav_file = AudioSegment.from_file("best_music/" + filename + ".wav", format="wav")

# Export it as an MP3 file
wav_file.export("best_music/"+ filename +".mp3", format="mp3")