from flask import send_from_directory
from flask import Flask, flash, request, redirect, url_for
from werkzeug.utils import secure_filename
from flask import render_template
from url_utils import get_base_url
import os
import torch
import json
import pandas as pd

# setup the webserver
# port may need to be changed if there are multiple flask servers running on same server
port = 12346
base_url = get_base_url(port)

# if the base url is not empty, then the server is running in development, and we need to specify the static folder so that the static files are served
if base_url == '/':
    app = Flask(__name__)
else:
    app = Flask(__name__, static_url_path=base_url+'static')

UPLOAD_FOLDER = 'static/uploads'
RESULTS_FOLDER = 'static/results'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
dummy_json = pd.read_json('File-1.json').to_dict()


app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024

model = torch.hub.load("ultralytics/yolov5", "custom", path = 'best4.pt', force_reload=True)
model.conf = 0.6
def loop_dict(dictionary, labels, key):
    resultList = []
    for label in labels:
        resultList.append(dictionary[label][key])
    return resultList

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route(f'{base_url}', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('uploaded_file', filename=filename))

    return render_template('home.html')


@app.route(f'{base_url}/uploads/<filename>', methods=['GET', 'POST'])
def uploaded_file(filename): #
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('uploaded_file', filename=filename))

    here = os.getcwd()
    image_path = os.path.join(here, app.config['UPLOAD_FOLDER'], filename)
    results = model(image_path, size=416)

    if len(results.pandas().xyxy[0]) >  0:
        results.print()
        result_dir = os.path.join(here, app.config['RESULTS_FOLDER'])
        results.save(save_dir=result_dir)
        result_filename = filename.split('.')[0]
        result_filename += ".jpg"
        def and_syntax(alist):
            if len(alist) == 1:
                alist = "".join(alist)
                return alist
            elif len(alist) == 2:
                alist = " and ".join(alist)
                return alist
            elif len(alist) > 2:
                alist[-1] = "and " + alist[-1]
                alist = ", ".join(alist)
                return alist
            else:
                return
        confidences = list(results.pandas().xyxy[0]['confidence'])
        # confidences: rounding and changing to percent, putting in function
        format_confidences = []
        for percent in confidences:
            format_confidences.append(str(round(percent*100)) + '%')
        format_confidences = and_syntax(format_confidences)

        labels = list(results.pandas().xyxy[0]['name'])
        #checks repeats
        label_reps=[]
        for i in labels:
            if i not in label_reps:
                label_reps.append(i)
            
        labels = label_reps
        
        for i in range(len(labels)): #renames to proper names
            if labels[i] == 'Shibu Inu':
                labels[i] = 'Shiba Inu'
            elif labels[i] == "Akita":
                labels[i] = "Akita Inu"
        dog_Names = labels
        dog_Info= loop_dict(dummy_json, labels, 'Personality')
        dog_desc= loop_dict(dummy_json, labels, 'Description')
        labels = and_syntax(labels)
        list_of_vowls = ['a','e','u', 'i', 'o','A','E','U','I','O']
        if any(x in list_of_vowls for x in labels[0]):
            a_an= 'an'
        else:
            a_an = 'a'
        # labels: sorting and capitalizing, putting into function
        return render_template('results.html', confidences=format_confidences, labels=labels,
                               old_filename=filename,
                               filename=result_filename,
                               dog_Names = dog_Names, #labels is being used in the and_syntax and would have a string instead of a list
                              dog_Personality=dog_Info,
                              dog_Description=dog_desc,
                              a_an=a_an)

    else:
        return render_template('results.html', labels='no dogs', old_filename=filename, filename=filename)

@app.route(f'{base_url}/test', methods=['GET', 'POST'])
def test():
    return render_template('index.html')

@app.route(f'{base_url}/uploads/<path:filename>')
def files(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

@app.route(f'{base_url}/info')
def info():
    return render_template('info.html')
# define additional routes here
# for example:
# @app.route(f'{base_url}/team_members')
# def team_members():
#     return render_template('team_members.html') # would need to actually make this page

if __name__ == '__main__':
    # IMPORTANT: change url to the site where you are editing this file.
    website_url = 'cocalc12.ai-camp.dev'
    print(f'Try to open\n\n    https://{website_url}' + base_url + '\n\n')
    app.run(host = '0.0.0.0', port=port, debug=True)
