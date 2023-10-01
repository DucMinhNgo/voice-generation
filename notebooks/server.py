#!/usr/bin/env python
# encoding: utf-8
import json
from flask import Flask, request, jsonify
import os

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

preload_models()
app = Flask(__name__)

@app.route('/', methods=['GET'])
def query_records():

    return jsonify({ 'message': 'OK'})

@app.route('/', methods=['PUT'])
def create_record():
    return jsonify({ 'message': 'OK'})

@app.route('/', methods=['POST'])
def update_record():
   text_prompt = """
        ♪ It's been a long day without you, my friend And I'll tell you all about it when I see you again, My name's Dustin Pro, My name's Dustin Pro ♪
        ♪ It's been a long day without you, my friend And I'll tell you all about it when I see you again, My name's Dustin Pro, My name's Dustin Pro ♪
    """
   audio_array = generate_audio(text_prompt)
   write_wav("output2.wav", SAMPLE_RATE, audio_array)

    # # # Load the WAV file
    # wav_file1 = AudioSegment.from_file("output2.wav", format="wav")

    # # # Export it as an MP3 file
    # wav_file1.export("../output1.mp3", format="mp3")
   return jsonify({ 'message': 'OK'})
app.run(debug=True)