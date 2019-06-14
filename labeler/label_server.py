from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse

import numpy as np
import tensorflow as tf

import os
import urllib
from collections import defaultdict

try:
    from urllib.parse import unquote, urlparse, parse_qs
except ImportError:
    from urlparse import unquote, urlparse, parse_qs

import json

from flask import Flask
from flask import request
from flask import url_for
from flask import jsonify
from flask_cors import CORS

from werkzeug.utils import secure_filename
import re
import base64

"""
Uploader variables
"""
UPLOAD_PATH = '/some-path'
ALLOWED_EXTENSIONS = set(['jpg', 'jpeg', 'png'])

"""
Predictor variables
"""
MODEL_FILE = "../model/output_graph.pb"
FILE_NAME = ""      
LABEL_FILE = "../model/output_labels.txt"

INPUT_HEIGHT = 299
INPUT_WIDTH = 299
INPUT_MEAN = 0
INPUT_STD = 255
INPUT_LAYER = "Placeholder"
OUTPUT_LAYER = "final_result"

app = Flask(__name__)
app.config["UPLOAD_PATH"] = UPLOAD_PATH
CORS(app)

class Predictor():
    def load_graph(self):
        graph = tf.Graph()
        graph_def = tf.GraphDef()

        with open(MODEL_FILE, "rb") as f:
            graph_def.ParseFromString(f.read())
        with graph.as_default():
            tf.import_graph_def(graph_def)

        return graph

    def read_tensor_from_image_file(
            self, 
            file_name,
            input_height=299,
            input_width=299,
            input_mean=0,
            input_std=255):
        input_name = "file_reader"
        output_name = "normalized"

        file_reader = tf.read_file(file_name, input_name)
        if file_name.endswith(".png"):
            image_reader = tf.image.decode_png(
                    file_reader, channels=3, name="png_reader")
        elif file_name.endswith(".gif"):
            image_reader = tf.squeeze(
                    tf.image.decode_gif(file_reader, name="gif_reader"))
        elif file_name.endswith(".bmp"):
            image_reader = tf.image.decode_bmp(file_reader, name="bmp_reader")
        else:
            image_reader = tf.image.decode_jpeg(
                    file_reader, channels=3, name="jpeg_reader")

        float_caster = tf.cast(image_reader, tf.float32)
        dims_expander = tf.expand_dims(float_caster, 0)
        resized = tf.image.resize_bilinear(dims_expander, [input_height, input_width])
        normalized = tf.divide(tf.subtract(resized, [input_mean]), [input_std])
        sess = tf.Session()
        result = sess.run(normalized)

        return result

    def load_labels(self, label_file):
        label = []
        proto_as_ascii_lines = tf.gfile.GFile(label_file).readlines()
        for l in proto_as_ascii_lines:
            label.append(l.rstrip())
        return label

@app.route("/predict", methods=["GET", "POST"])
def predict():
    image_data = request.json['image']
    image_base_64 = image_data[22:]

    with open("base64data", "wb") as fh:
        fh.write(image_data)

    with open("uploaded_image.png", "wb") as fh:
        fh.write(base64.b64decode(image_base_64))

    main_predictor = Predictor()


    data = request.args

    file_name = "./uploaded_image.png" 

    graph = main_predictor.load_graph()
    t = main_predictor.read_tensor_from_image_file(
            file_name = file_name,
            input_height=INPUT_HEIGHT,
            input_width=INPUT_WIDTH,
            input_mean=INPUT_MEAN,
            input_std=INPUT_STD)
    input_name = "import/" + INPUT_LAYER
    output_name = "import/" + OUTPUT_LAYER
    input_operation = graph.get_operation_by_name(input_name)
    output_operation = graph.get_operation_by_name(output_name)

    with tf.Session(graph=graph) as sess:
        results = sess.run(output_operation.outputs[0], {
            input_operation.outputs[0]: t    
            })
        results = np.squeeze(results)

    top_k = results.argsort()[-5:][::-1]
    labels = main_predictor.load_labels(LABEL_FILE)
    label_results = defaultdict(str)

    for i in top_k:
        label_results[labels[i]] = str(results[i])

    return jsonify(label_results)

if __name__ == '__main__':
    port = os.environ.get('PORT', 5000)
    app.run(host='127.0.0.1', port = port)