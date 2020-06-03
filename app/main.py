from flask import Flask, render_template, request, redirect
app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/upload', methods=["GET", "POST"])
def upload_image():
    if request.method == "POST":
        # Check if file is empty
        if request.files:
            image = request.files["image"]
            #TODO: remove after testing
            print("image is valid")
            print(image)
            return redirect(request.url)

    return render_template("public/upload_image.html")