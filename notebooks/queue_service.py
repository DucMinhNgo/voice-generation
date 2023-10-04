import redis
import multiprocessing
import time
import os
import uuid
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
from IPython.display import Audio
import nltk  # we'll use this to split into sentences
import numpy as np
from bark.generation import (
    generate_text_semantic,
    preload_models,
)
from bark.api import semantic_to_waveform
from bark import generate_audio, SAMPLE_RATE
from scipy.io.wavfile import write as write_wav
from pydub import AudioSegment

# Function to process a single item from the queue
def process_item(item):
    # Replace this with your actual processing logic
    print(f"Processing item: {item}")
    text_prompt = """
        ♪ Ohayô, oyasumi, Konnichiwa, Konbanwa, Ohayô, oyasumi, Konnichiwa, Konbanwa ♪
        ♪ Itte Kimasu, Itte rasshai, Tadaima, Okaerinasai, Itadakimasu, Gochisôsama, Rararararara arigatô, Sayônara oyasumi, Mata ashita, Kinô no yume no tsuzuki o mini yukô ♪
    """
    filename = str(uuid.uuid4())
    audio_array = generate_audio(text_prompt)
    Audio(audio_array, rate=SAMPLE_RATE)

    write_wav("../wav_gen/" + filename + ".wav", SAMPLE_RATE, audio_array)
    wav_file = AudioSegment.from_file("../wav_gen/" + filename + ".wav", format="wav")

    # Export it as an MP3 file
    wav_file.export("../mp3_gen/"+ filename +".mp3", format="mp3")

# Function to pull and process items from the Redis queue
def worker(queue_name):
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    while True:
        # Blocking pop operation from the queue
        item = redis_client.blpop(queue_name, timeout=0)
        
        if item:
            item = item[1].decode('utf-8')  # Convert bytes to string
            process_item(item)

if __name__ == "__main__":
    queue_name = "my_queue"  # Replace with your Redis queue name
    num_processes = 1  # Number of worker processes
    preload_models()
    
    # Create and start worker processes
    processes = []
    for _ in range(num_processes):
        p = multiprocessing.Process(target=worker, args=(queue_name,))
        processes.append(p)
        p.start()
    
    # Wait for all processes to finish
    for p in processes:
        p.join()

