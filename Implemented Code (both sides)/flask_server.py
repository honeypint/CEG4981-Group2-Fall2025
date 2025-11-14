#!/usr/bin/env python3
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
import os

RESULT_DIR = "/home/Group2/decrypted_images"

app = Flask(__name__)
CORS(app)

@app.route("/files", methods=["GET"])
def list_files():
    files = os.listdir(RESULT_DIR)
    return jsonify(files)

@app.route("/files/<path:filename>", methods=["GET"])
def serve_file(filename):
    return send_from_directory(RESULT_DIR, filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
