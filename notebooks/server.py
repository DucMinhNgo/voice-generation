#!/usr/bin/env python
# encoding: utf-8
import json
from flask import Flask, request, jsonify
import os
import redis
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
import uuid

os.environ["CUDA_VISIBLE_DEVICES"] = "0"
queue_name = 'my_queue'
redis_client = redis.Redis(host='localhost', port=6379, db=0)

app = Flask(__name__)

@app.route('/', methods=['GET'])
def query_records():

    return jsonify({ 'message': 'OK'})

@app.route('/', methods=['PUT'])
def create_record():
    return jsonify({ 'message': 'OK'})

@app.route('/', methods=['POST'])
def update_record():
    body = json.loads(request.data)
    text = ""
    for lyric in body['lyrics']:
        text += "♪ " + lyric + " ♪\n"

    text_prompt = f"""
      {text}
    """
    print (text_prompt)
    request_id = str(uuid.uuid4())
    data = {
       'request_id': request_id,
       'text_prompt': text_prompt,
    }
    redis_client.set(request_id, json.dumps({
        'data': data,
        'status': 'in-progress'
    }))
    redis_client.rpush(queue_name, json.dumps(
        data
    ))

    return jsonify({ 'message': 'OK', 'data': data })

@app.route('/get-list', methods=['GET'])
def get_list():
    keys = redis_client.keys()
    print (keys[0].decode("utf-8"))
    print (json.loads(redis_client.get(keys[0])))
    filter_arr = []
    for key in keys:
        if key.decode("utf-8") != queue_name:
          data = json.loads(redis_client.get(keys[0]))
          filter_arr.append({
              'key': key.decode("utf-8"),
              'data': {
                  'request_id': data,
              }
            })
    return jsonify(result={ 'message': 'OK', 'data': filter_arr})

app.run(debug=True)