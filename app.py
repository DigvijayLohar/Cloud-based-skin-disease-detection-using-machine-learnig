from __future__ import division, print_function
# coding=utf-8
from flask import Flask , render_template  , request , send_file ,flash,session

import os
from PIL import Image

import numpy as np

# Keras

from keras.models import load_model
from keras.preprocessing import image
# Flask utils
from flask import Flask, redirect, url_for, request, render_template
import os
import uuid
import flask
import urllib
from keras.models import load_model

from keras.preprocessing.image import load_img , img_to_array
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
# Define a flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)
# Databade COnnection
MONGO_URI ="mongodb+srv://vishal:pass123@cluster0.wai525o.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = MongoClient(MONGO_URI)
db = client.get_database('youtube')
User = db.users
UserCU = db.contact
print('MG Database Connected')
# Model saved with Keras model.save()
MODEL_PATH = 'model2.h5'

# Load your trained model
model = load_model(MODEL_PATH)

print('Model loaded. Start serving...')


ALLOWED_EXT = set(['jpg']) 
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXT

classes = ['Actinic keratoses', 'Basal cell carcinoma', 'Benign keratosis-like lesions', 'Dermatofibroma', 'Melanoma', 'Melanocytic nevi', 'Vascular lesions']

def model_predict(img_path, model):
    img = image.load_img(img_path, target_size=(32, 32))  # image size 32,32
    img = image.img_to_array(img)    # convert image to array
    img = img.reshape(1 , 32 ,32 ,3)  #reshaping image in 32,32 with  rgb colour

    img = img.astype('float32')
    img = img/255.0     # Here we convert the Array value into 0 - 1 between;
    preds = model.predict(img)
    dict_result = {}
    for i in range(7):
        dict_result[preds[0][i]] = classes[i]  # preds =[0, 0, 0 ,0,100,0] 

    res = preds[0]  
    res.sort()       # res = [0,0,0,0,100]
    res = res[::-1]  #res = [ 100,0,0,0,0]
    prob = res[:3]   # prob = [100,0,0]
    
    class_result = []
    for i in range(1):
        class_result.append(dict_result[prob[i]])   # here key pass and take predic
    return class_result 


@app.route('/', methods=['GET'])
def html():
    # Main page
    if 'user_id' in session:
        return redirect(url_for('home')) 
    return render_template('html.html')

@app.route('/index2', methods=['GET','POST'])
def index2():
    if 'user_id' not in session:
        return redirect(url_for('/'))
    # Main page
    return render_template('index2.html')

@app.route('/About', methods=['GET','POST'])
def About():
    return render_template('About.html')


@app.route('/contact', methods=['GET','POST'])
def contact():
    return render_template('contact.html')

@app.route('/upload' , methods = ['GET' , 'POST'])
def upload():
    if 'user_id' not in session:
        return render_template('html.html')
    error = ''
    target_img = os.path.join(os.getcwd() , 'static')
    if request.method =='POST':
        if(request.form):
            link = request.form.get('link')
            try :
                resource = urllib.request.urlopen(link)
                unique_filename = str(uuid.uuid4())
                filename = unique_filename+".jpg"
                img_path = os.path.join(target_img , filename)
                output = open(img_path , "wb")
                output.write(resource.read())
                output.close()
                img = filename

                class_result  = model_predict(img_path , model)

                predictions = {
                      "class1":class_result[0]
                }

            except Exception as e : 
                print(str(e))
                error = 'This image from this site is not accesible or inappropriate input'

            if(len(error) == 0):
                return  render_template('upload.html' , img  = img , predictions = predictions)
            else:
                return render_template('home.html' , error = error) 

            
        elif (request.files):
            file = request.files['file']
            if file and allowed_file(file.filename):
                file.save(os.path.join(target_img , file.filename))
                img_path = os.path.join(target_img , file.filename)
                img = file.filename

                class_result  = model_predict(img_path , model)

                predictions = {
                      "class1":class_result[0]
                }

            else:
                error = "Please upload images of jpg , jpeg and png extension only"

            if(len(error) == 0):
                return  render_template('upload.html' , img  = img , predictions = predictions)
            else:
                return render_template('home.html' , error = error)

    else:
        return render_template('home.html')

@app.route('/login',methods=['GET', 'POST'])
def login():
     error = None
     if request.method == 'GET':  # Check if the request method is GET
        return render_template('login.html') 
    
     email = request.form.get('email')
     password = request.form.get('password')

    # Query the database for the user
     user = User.find_one({'email': email})

     if user:
        # Check if the provided password matches the hashed password in the database
        if (password == user['password']):
            # Authentication successful, store user ID in session
            session['user_id'] = str(user['_id'])
            return redirect('/home')
        else:
            error='Invalid username or password'
            return render_template('login.html', error=error) 
     else:
        error="user not found"
        return render_template('login.html', error=error) 

@app.route('/register',methods=['GET', 'POST'])
def register():
    error=None
    if request.method == 'GET':  # Check if the request method is GET
        return render_template('register.html') 
    email = request.form.get('email')
    password = request.form.get('password')
    username = request.form.get('username')
   

    # Check if the username already exists in the database
    if User.find_one({'email': email}):
        error="Username already exists,"
        return render_template('/register.html',error=error)
    # Insert the new user into the database
    user_data = {'username': username, 'password': password,'email': email}
    User.insert_one(user_data)
    user=User.find_one({'email': email})
    session['user_id'] = str(user['_id'])
    error="Registration successful! You can now login."
    return redirect('/home')


@app.route('/home', methods=['GET','POST'])
def home():
    if 'user_id' not in session:
        return render_template('html.html')
    return render_template('home.html')

@app.route('/logout')
def logout():
    session.clear()
    return render_template('html.html')

@app.route('/contactform',methods=['POST'])
def contactform():
    if request.method == 'POST': # Check if the request method is GET
         email = request.form.get('email')
         message = request.form.get('message')
         username = request.form.get('username')
         user_data = {'email':email,'username':username,'message':message}
         try:
            UserCU.insert_one(user_data)
            return redirect('/contact')
         except DuplicateKeyError as e:
            print("Duplicate key error:", e)
            return render_template('contact.html')
    else:
        return render_template('contact.html')


@app.route('/output', methods=['GET','POSt'])
def output():
    classpred = request.args.get('classpred')
    return render_template('output.html', classpred=classpred)


if __name__ == "__main__":
    app.run(host= "0.0.0.0")