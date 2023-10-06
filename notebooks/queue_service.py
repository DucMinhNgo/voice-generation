import redis
import multiprocessing
import time
import json
import os
import uuid
os.environ["CUDA_VISIBLE_DEVICES"] = "1"
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

redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Function to process a single item from the queue
def process_item(item):
    data = json.loads(item)
    print (data['request_id'])
    text_prompt = data["text_prompt"]

    keyname = str(uuid.uuid4())
    for i in range(5):
        filename = keyname + "-" + str(i + 1)
        audio_array = generate_audio(text_prompt)
        Audio(audio_array, rate=SAMPLE_RATE)

        write_wav("../wav_gen/" + filename + ".wav", SAMPLE_RATE, audio_array)
        wav_file = AudioSegment.from_file("../wav_gen/" + filename + ".wav", format="wav")

        # Export it as an MP3 file
        wav_file.export("../mp3_gen/"+ filename +".mp3", format="mp3")
        
        data_get_from_redis = json.loads(redis_client.get(data['request_id']))
        results = data_get_from_redis['data']['results']
        results.append(filename +".mp3")
        data_get_from_redis['data']['results'] = results

        print ('data_get_from_redis')
        print (data['request_id'])
        print (data_get_from_redis)
        redis_client.set(data['request_id'], json.dumps(data_get_from_redis))
    # update status done
    data_get_from_redis = json.loads(redis_client.get(data['request_id']))
    data_get_from_redis['data']['status'] = 'completed'
    redis_client.set(data['request_id'], json.dumps(data_get_from_redis))

# Function to pull and process items from the Redis queue
def worker(queue_name):
    while True:
        # Blocking pop operation from the queue
        item = redis_client.blpop(queue_name, timeout=0)
        
        if item:
            item = item[1].decode('utf-8')  # Convert bytes to string
            process_item(item)

if __name__ == "__main__":
    queue_name = "my_queue"  # Replace with your Redis queue name
    num_processes = 2  # Number of worker processes
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

