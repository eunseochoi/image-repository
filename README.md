# shopify-image-repository

This is an image repository which has two main functionalities:
1. Adding Image(s)
  - User can only add `JPEG`, `JPG`, `PNG`, `GIF` files
  - Private/public permissions -> when an image is uploaded, there should be a user information associated with the object.
  - bulk images
  - secure uploading -> GCP (Google Storage Bucket)  
    a) ensuring file has a name  
    b) ensuring file type is allowed  
    c) ensuring filename is allowed  
    d) ensuring filesize is allowed  

2. Deleting Image(s)
  - One / bulk / selected / all images
  - Prevent user deleting images from another user
  - secure deletion of images


**Workflow:**

1. Setup basic flask application
2. Configure GCP
3. Make a Image model  
  a) image_id  
  b) date_uploaded  
  c) file_name  
  d) blob_path  
4. Store Firestore document for every file uploaded
5. Implement Delete Functionality  
  a) single delete by ID  
  b) bulk delete  
6. Incorporate user information into Firestore
7. Check if user credentials match (uploaded image vs. Image they wish to delete)
8. Unit tests
9. Documentation