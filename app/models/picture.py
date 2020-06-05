import datetime
import logging
import os

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

from fireo.models import Model
from fireo import fields

from google.cloud import storage

from logger import ColoredLogger

# Use the application default credentials
CLOUD_STORAGE_BUCKET = os.environ.get("CLOUD_STORAGE_BUCKET")
storage_client = storage.Client()

cred = credentials.ApplicationDefault()
firebase_admin.initialize_app(cred, {"projectId": os.environ.get("PROJECT_ID"),})

logger = logging.getLogger("logger")
db = firestore.client()


class Picture(Model):
    image_id = fields.TextField()
    date_added = fields.DateTime()
    file_name = fields.TextField()
    blob_name = fields.TextField()
    user_id = fields.TextField()

    def __init__(self, image_id="", file_name="", blob_name="", user_id=""):
        self.image_id = image_id
        self.date_added = datetime.datetime.now()
        self.file_name = file_name
        self.blob_name = blob_name
        self.user_id = user_id

    def add_image(self, image_object, user_id):
        try:
            bucket = storage_client.get_bucket(CLOUD_STORAGE_BUCKET)
            # In case users upload pictures with the same file name, concatenate user's id with file name
            blob = bucket.blob(user_id + "_" + self.file_name)
            blob.upload_from_string(
                image_object.read(), content_type=image_object.content_type
            )
            self.blob_name = blob.name
            self.user_id = user_id
            logger.info("Successfully uploaded image to Google Cloud Bucket")

            # Store object in Firestore to keep track of ID's
            db.collection("Images").document(self.image_id).set(self.__dict__)
            logger.info(
                "Successfully stored document with image_id: {} in Firestore".format(
                    self.image_id
                )
            )
            return True
        except Exception as e:
            logger.error(str(e))
            return False

    def delete_image(self, image_id, user_id):
        # Find Firestore document using image_id
        image = db.collection("Images").document(image_id)
        bucket = storage_client.get_bucket(CLOUD_STORAGE_BUCKET)
        image_dict = image.get().to_dict()

        # Check if the user credentials match the uploaded picture they wish to delete
        if image_dict["user_id"] != user_id:
            logger.error("This user does not have permission to delete the image")
            return False
        try:
            # Delete blob from Google Cloud bucket
            bucket.delete_blob(image_dict["blob_name"])
            logger.debug("Deleted Blob: {}".format(image_dict["blob_name"]))

            # Delete Firestore
            image.delete()
            logger.debug(
                "Firestore document deleted for image_id: {}".format(
                    image_dict["image_id"]
                )
            )
            return True
        except Exception as e:
            logger.debug(str(e))
            logger.error("Cannot find blob in the bucket")
            return False

    def bulk_delete(self, user_id):
        images = db.collection("Images").stream()
        count = 0
        try:
            for image in images:
                is_deleted = self.delete_image(image.get("image_id"), user_id)
                if is_deleted:
                    db.collection("Images").document(image.get("image_id")).delete()
                    count += 1
                    logger.debug("Deleted {} images".format(count))
            return True
        except Exception as e:
            logger.error("Bulk-Delete Exception: {}".format(str(e)))
            return False
