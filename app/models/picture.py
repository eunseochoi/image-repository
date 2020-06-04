import datetime
import os

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

from fireo.models import Model
from fireo import fields

from google.cloud import storage

# Use the application default credentials
CLOUD_STORAGE_BUCKET = os.environ.get('CLOUD_STORAGE_BUCKET')
storage_client = storage.Client()

cred = credentials.ApplicationDefault()
firebase_admin.initialize_app(cred, {
  'projectId': os.environ.get('PROJECT_ID'),
})

db = firestore.client()

class Picture(Model):
    image_id = fields.TextField()
    date_added = fields.DateTime()
    file_name = fields.TextField()
    blob_path = fields.TextField()

    def __init__(self, image_id="", file_name="", blob_path=""):
        self.image_id = image_id
        self.date_added = datetime.datetime.now()
        self.file_name = file_name
        self.blob_path = blob_path

    def add_image(self, image_object):
        bucket = storage_client.get_bucket(CLOUD_STORAGE_BUCKET)
        blob = bucket.blob(self.file_name)
        blob.upload_from_string(image_object.read(), content_type=image_object.content_type)
        self.blob_path = blob.name
        print("successfully uploaded image to GCP")
        
        # Store object in Firestore to keep track of ID's
        print("IMAGE_ID: ", self.image_id)
        db.collection("Images").document(self.image_id).set(self.__dict__)
        print("Successfully stored document in Firestore")
        print(self.__dict__)
    
    def delete_image(self, image_id):
        # Find Firestore document using image_id
        image = db.collection("Images").document(image_id)
        bucket = storage_client.get_bucket(CLOUD_STORAGE_BUCKET)
        image_dict = image.get().to_dict()
        try:
            bucket.delete_blob(image_dict["blob_path"])
            print("======Deleted Blob=======")
            # Delete Firestore
            image.delete()
            return True
        except Exception as e:
            print(str(e))
            print("Cannot find blob in the bucket")
            return False
        
    def bulk_delete(self):
        images = db.collection("Images").stream()
        count = 0
        try:
            for image in images:
                self.delete_image(image.get("image_id"))
                db.collection("Images").document(image.get("image_id")).delete()
                count += 1
            print("Deleted {} images".format(count))
            return True
        except Exception as e:
            print("Bulk-Delete Exception: ", str(e))
            return False