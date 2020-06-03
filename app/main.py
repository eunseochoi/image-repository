import logging
import os
import uuid

from flask import Flask, redirect, render_template, request

from google.cloud import storage

from models.image import Image

# constants
CLOUD_STORAGE_BUCKET = os.environ.get('CLOUD_STORAGE_BUCKET')
storage_client = storage.Client()

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/upload', methods=["GET", "POST"])
def upload_image():
    if request.method == "POST":
        if request.files:
            image_object = request.files["image"]
            image = Image(str(uuid.uuid4()), image_object.filename)
            image.add_image(image_object)

    return render_template("public/upload_image.html")

@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500

if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    app.run(host='127.0.0.1', port=5000, debug=True)