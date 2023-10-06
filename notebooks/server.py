#!/usr/bin/env python
# encoding: utf-8
import json
from flask import Flask, request, jsonify, send_file
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
from flask_cors import CORS

os.environ["CUDA_VISIBLE_DEVICES"] = "0"
queue_name = 'my_queue'
redis_client = redis.Redis(host='localhost', port=6379, db=0)

app = Flask(__name__)
CORS(app)

@app.route('/', methods=['GET'])
def query_records():
  return jsonify({ 'message': 'OK'})

@app.route("/get-file/<string:filename>")
def return_file(filename):
  print (filename)
  return send_file('../mp3_gen/' + filename)

@app.route("/get-best-file/<string:filename>")
def return_best_file(filename):
  print (filename)
  return send_file('../mp3_gen/best_music/' + filename)

@app.route("/get-best-music")
def get_best_music():
  directory_path = '../mp3_gen/best_music'
  files_only = [f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))]
  return jsonify({
     'message': 'OK',
     'results': files_only
  }) 

# @app.route('/', methods=['PUT'])
# def create_record():
#     return jsonify({ 'message': 'OK'})

@app.route('/', methods=['POST'])
def create_record():
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
      'lyrics': body['lyrics'],
      'text_prompt': text_prompt,
      'status': 'in-progress',
      'results': [],
    }
    redis_client.set(request_id, json.dumps({
        'data': data,
    }))
    redis_client.rpush(queue_name, json.dumps(
        data
    ))

    return jsonify({ 'message': 'OK', 'data': data, 'status': 200 })

@app.route("/get-detail/<string:id>")
def get_detail(id):
   return jsonify({
    'message': 'OK',
    'data': {
       'key': id,
       'data': {
          'request_id': json.loads(redis_client.get(id)),
       }
    } 
   })

@app.route('/get-list', methods=['GET'])
def get_list():
    keys = redis_client.keys()
    filter_arr = []
    for key in keys:
        if key.decode("utf-8") != queue_name:
          data = json.loads(redis_client.get(key))
          filter_arr.append({
              'key': key.decode("utf-8"),
              'data': {
                  'request_id': data,
              }
            })
    return jsonify(result={ 'message': 'OK', 'data': filter_arr, 'status': 200})
  

@app.route('/remove-all', methods=['DELETE'])
def remove_all():
  keys = redis_client.keys()
  for key in keys:
     redis_client.delete(key)
  return jsonify(result={ 'message': 'OK'}) 

app.run(debug=True)