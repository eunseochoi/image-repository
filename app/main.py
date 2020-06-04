from http import HTTPStatus
import logging
import os
import uuid

from flask import jsonify, Flask, redirect, render_template, request

from google.cloud import storage

from models.picture import Picture
from models.response import response

# constants
CLOUD_STORAGE_BUCKET = os.environ.get('CLOUD_STORAGE_BUCKET')
storage_client = storage.Client()

app = Flask(__name__)
#TODO: configure max size for image
app.config["MAX_IMAGE_FILESIZE"] = 0.5 * 1024 * 1024

@app.route('/upload', methods=["POST"])
def upload_image():
    if request.files.getlist("images[]"):
        files = request.files.getlist("images[]")
        for file_obj in files:
            image = Picture(str(uuid.uuid4()), file_obj.filename)
            image.add_image(file_obj)
    resp = response(HTTPStatus.CREATED, "Successfully uploaded {} images".format(len(files)))
    return jsonify(resp), HTTPStatus.CREATED

@app.route('/delete', methods=["DELETE"])
def delete_image():
    if request.form.get("image_id"):
        file_name = request.form.get("image_id")
        deleted = Picture().delete_image(file_name)
    elif request.args.get("bulk"):
        deleted = Picture().bulk_delete()
    else:
        resp = response(HTTPStatus.BAD_REQUEST, "Image id not provided, nor bulk_delete option was not selected")
        return jsonify(resp), HTTPStatus.BAD_REQUEST
    
    if deleted:
        resp = response(HTTPStatus.MOVED_PERMANENTLY, "Successfully deleted image")
        return jsonify(resp), HTTPStatus.MOVED_PERMANENTLY
    resp = response(HTTPStatus.INTERNAL_SERVER_ERROR, "Could not delete image")
    return jsonify(resp), HTTPStatus.INTERNAL_SERVER_ERROR

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