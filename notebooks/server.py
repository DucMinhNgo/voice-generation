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
import datetime
from pydub import AudioSegment

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

@app.route("/get-melody-file/<string:filename>")
def return_melody_file(filename):
  print (filename)
  return send_file('../mp3_gen/best_music/melody/' + filename)

@app.route("/get-melody-music")
def get_melody_music():
  directory_path = '../mp3_gen/best_music/melody'
  files_only = [f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))]
  return jsonify({
     'message': 'OK',
     'results': files_only
  }) 

# @app.route('/', methods=['PUT'])
# def create_record():
#     return jsonify({ 'message': 'OK'})

@app.route('/melody', methods=['POST'])
def create_melody():
  body = json.loads(request.data)
  request_id = 'melody-' + str(uuid.uuid4())
  print (body)
  data = {
    'request_id': request_id,
    'lyrics': body['lyrics'],
    # 'text_prompt': text_prompt,
    'status': 'in-progress',
    'results': [],
  }
  # redis_client.set(request_id, json.dumps({
  #     'data': data,
  # }))
  redis_client.rpush('my_melody', json.dumps(
      data
  ))
  return jsonify({
    'message': 'OK', 
  })

@app.route('/mix', methods=['POST'])
def mix_music():
  body = json.loads(request.data)
  request_id = 'mix-' + str(uuid.uuid4()) 
  file_name = 'mix-' + str(uuid.uuid4())
  results = []
  i = 0
  lyrics = [body['music_id']]
  for melody in body['melody']:
    i += 1
    audio1 = AudioSegment.from_mp3("../mp3_gen/" + body['music_id'])
    audio2 = AudioSegment.from_mp3("../mp3_gen/best_music/melody/" + melody)

    # Ensure both audio segments are 14 seconds long
    target_duration = 15 * 1000  # 14 seconds in milliseconds
    audio1 = audio1[:target_duration]
    audio2 = audio2[:target_duration]

    # Mix the two audio segments
    mixed_audio = audio1.overlay(audio2)
    result = file_name + "-" + str(i) + '.mp3'
    lyrics.append(melody)

    # Export the mixed audio as an MP3 file
    mixed_audio.export("../mp3_gen/" + file_name + "-" + str(i) + '.mp3', format="mp3")
    results.append(result)
  
  data = {
      'request_id': request_id,
      'lyrics': lyrics,
      'text_prompt': str(lyrics),
      'status': 'completed',
      'results': results,
      'created_at': str(datetime.datetime.now()),
    }
  redis_client.set(request_id, json.dumps({
        'data': data,
    }))
  return jsonify({ 'message': 'OK', 'data': data, 'status': 200 })

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
      'created_at': str(datetime.datetime.now()),
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
        if key.decode("utf-8") != queue_name and key.decode("utf-8") != 'my_melody' and 'melody' not in key.decode("utf-8"):
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