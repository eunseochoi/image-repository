from http import HTTPStatus
import logging
import os
import uuid

from flask import jsonify, Flask, redirect, render_template, request

from google.cloud import storage

from models.picture import Picture
from models.response import response

# constants
CLOUD_STORAGE_BUCKET = os.environ.get("CLOUD_STORAGE_BUCKET")
storage_client = storage.Client()

app = Flask(__name__)
app.config["MAX_IMAGE_FILESIZE"] = 0.5 * 1024 * 1024
app.config["ALLOWED_IMAGE_EXTENSIONS"] = ["JPEG", "JPG", "PNG", "GIF"]

logger = logging.getLogger("logger")


@app.route("/upload", methods=["POST"])
def upload_image():
    user_id = request.form.get("user_id")
    if request.files.getlist("images"):
        files = request.files.getlist("images")
        for file_obj in files:
            is_valid, error_msg = _is_file_valid(file_obj, request)
            if False in is_valid.values():
                resp = response(HTTPStatus.BAD_REQUEST, error_msg[0])
                return jsonify(resp), HTTPStatus.BAD_REQUEST
            image = Picture(str(uuid.uuid4()), file_obj.filename)
            uploaded = image.add_image(file_obj, user_id)
    if uploaded:
        resp = response(
            HTTPStatus.CREATED, "Successfully uploaded {} images".format(len(files))
        )
        return jsonify(resp), HTTPStatus.CREATED
    else:
        resp = (
            response(HTTPStatus.NO_CONTENT, "Could not upload image"),
            HTTPStatus.NO_CONTENT,
        )


@app.route("/delete", methods=["DELETE"])
def delete_image():
    user_id = request.form.get("user_id")
    if request.form.get("image_id"):
        file_name = request.form.get("image_id")
        deleted = Picture().delete_image(file_name, user_id)
    elif request.args.get("bulk"):
        deleted = Picture().bulk_delete(user_id)
    else:
        resp = response(
            HTTPStatus.BAD_REQUEST,
            "Image id not provided, nor bulk_delete option was not selected",
        )
        return jsonify(resp), HTTPStatus.BAD_REQUEST

    if deleted:
        resp = response(HTTPStatus.MOVED_PERMANENTLY, "Successfully deleted image(s)")
        return jsonify(resp), HTTPStatus.MOVED_PERMANENTLY
    resp = response(HTTPStatus.INTERNAL_SERVER_ERROR, "Could not delete image")
    return jsonify(resp), HTTPStatus.INTERNAL_SERVER_ERROR


def _is_file_valid(file_obj, request):
    # Private helper function to validate file type, file name and file size
    is_valid = {"name": True, "type": True, "size": True}
    error_msg = []
    ext = file_obj.filename.rsplit(".", 1)[1]

    # File Name Check
    if file_obj.filename == "" or "." not in file_obj.filename:
        is_valid["valid_name"] = False
        error_msg.append("File name not valid")
        return is_valid, error_msg

    # File Type Check (only images/gifs are allowed)
    if ext.upper() not in app.config["ALLOWED_IMAGE_EXTENSIONS"]:
        is_valid["type"] = False
        error_msg.append("File type not allowed")
        return is_valid, error_msg

    # File Size Check, if size exceeds, do not upload
    if "file_size" in request.cookies:
        file_size = request.cookies["file_size"]
        if int(file_size) <= app.config["MAX_IMAGE_FILESIZE"]:
            is_valid["size"] = False
            error_msg.append("File size exceeded maximum size of 500,000 bytes")

    return is_valid, error_msg


if __name__ == "__main__":
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    logger.info("Running App on http://localhost:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)
