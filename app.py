from flask import Flask, render_template, request, redirect, url_for, jsonify, session, abort
from models import Database
from authlib.integrations.flask_client import OAuth
from loginpass import create_flask_blueprint, GitHub, Google, Gitlab, Discord
from dotenv import load_dotenv
from datetime import datetime
import pyrebase
import os

app = Flask(__name__)
oauth = OAuth(app)
if os.path.isfile('.env'):
    load_dotenv()
config = dict(os.environ)

app.secret_key = os.getenv("SECRET_KEY")
backends = [GitHub, Google, Gitlab, Discord]
firebaseConfig = {
    "apiKey": os.getenv("FIREBASE_API_KEY"),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
    "databaseURL": os.getenv("FIREBASE_DATABASE_URL"),
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
}
firebase = pyrebase.initialize_app(firebaseConfig)
storage = firebase.storage()
database = Database(storage)

@app.route('/')
def index():
    if 'user' in session:
        user = database.getUser(session['user']['_id'])
        if user["type"] == "doctor":
            return render_template('doctors/doctor.html', user = user)
        return render_template('patients/user.html', user = user)
    return render_template('index.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user' in session:
        if request.method == 'GET':
            user = database.getUser(session['user']['_id'])
            return render_template('settings.html', user = user)
        else:
            data = request.form.to_dict()
            data = dict(data)
            # print(data)
            allergies = []
            e = []
            for keys in data:
                if keys.startswith("allergy"):
                    allergies.append(data[keys])
                    e.append(keys)
            for i in e:
                data.pop(i)
            data["allergies"] = allergies
            print(data)
            database.updateUser(session['user']['_id'], data)

    return redirect(url_for('index'))

@app.route('/doctors', methods=['GET', 'POST', 'DELETE'])
def doctors():
    if 'user' not in session:
        return
    if request.method == 'DELETE':
        doctorId = request.form.get("doctorId")
        doc = database.getUser(doctorId)
        user = database.getUser(session['user']['_id'])
        if doc and doc["type"] == "doctor" and doc["_id"] in user["doctors"]:
            database.removeDoctor(session['user']['_id'], doctorId)
        return jsonify({"success": "Doctor removed"})
    elif request.method == 'GET':
        user = database.getUser(session['user']['_id'])
        if user["type"] == "user":
            doctorIDs = user["doctors"]
            doctors = [database.getUser(d) for d in doctorIDs]
            return render_template('patients/doctors.html', doctors = doctors, user = user)
    elif request.method == 'POST':
        doctorId = request.form.get("doctorId")
        doc = database.getUser(doctorId)
        user = database.getUser(session['user']['_id'])
        if doc:
            if doc["type"] == "doctor":
                if doc["_id"] not in user["doctors"]:
                    database.addDoctor(session['user']['_id'], doctorId)
                return redirect(url_for('doctors'))
            else:
                return jsonify({"error": "User is not a doctor"})
        else:
            return jsonify({"error": "User does not exist"})

@app.route('/patients', methods=['GET', 'POST', 'DELETE'])
def patients():
    if 'user' not in session:
        return
    if request.method == 'DELETE':
        patientId = request.form.get("patientId")
        print(patientId)
        patient = database.getUser(patientId)
        user = database.getUser(session['user']['_id'])
        if (
            patient
            and patient["type"] == "user"
            and patient["_id"] in user["patients"]
        ):
            database.removePatient(session['user']['_id'], patientId)
        return jsonify({"success": "Patient removed"})
    elif request.method == 'GET':
        user = database.getUser(session['user']['_id'])
        if user["type"] == "doctor":
            patientsIDs = user["patients"]
            patients = [database.getUser(d) for d in patientsIDs]
            return render_template('doctors/patients.html', patients = patients, user = user)
    elif request.method == 'POST':
        patientsId = request.form.get("patientId")
        patient = database.getUser(patientsId)
        user = database.getUser(session['user']['_id'])
        if patient:
            if patient["type"] == "user":
                if patient["_id"] not in user["patients"]:
                    database.addPatient(session['user']['_id'], patientsId)
                return redirect(url_for('patients'))
            else:
                return jsonify({"error": "User is not a patient"})
        else:
            return jsonify({"error": "User does not exist"})

@app.route('/doctor/<id>')
def doctorView(id):
    if 'user' in session:
        user = database.getUser(session['user']['_id'])
        if user["type"] == "user":
            doctor = database.getUser(id)
            return render_template('patients/doctorview.html', user = user, doctor = doctor)
        return redirect(url_for('index'))
    return redirect(url_for('index'))

@app.route('/patient/<id>')
def patientView(id):
    if 'user' in session:
        user = database.getUser(session['user']['_id'])
        if user["type"] == "doctor":
            patient = database.getUser(id)
            return render_template('doctors/patientview.html', user = user, patient = patient)
        return redirect(url_for('index'))
    return redirect(url_for('index'))

@app.route('/reports/medical', methods=['GET'])
def medicalReport():
    if 'user' not in session:
        return
    user = database.getUser(session['user']['_id'])
    reports = []
    if user["type"] == "user":
        for i in user["medicalReports"]:
            i['by'] = database.getUser(i['by'])
            reports.append(i)
        return render_template('patients/reports/medical/medical.html', user = user, reports = reports)
    else:
        for i in user["medicalReports"]:
            i['for'] = database.getUser(i['for'])
            reports.append(i)
        return render_template('doctors/reports/medical/medical.html', user = user, reports = reports)

@app.route('/reports/medical/new', methods=['GET', 'POST'])
def newMedicalReport():
    if 'user' not in session:
        return redirect(url_for('index'))
    user = database.getUser(session['user']['_id'])
    if user["type"] == "doctor":
        if request.method == 'GET':
            patients = [database.getUser(i) for i in user["patients"]]
            user["patients"] = patients
            return render_template('doctors/reports/medical/add.html', user = user)
        else:
            data = request.form.to_dict()
            data = dict(data)
            medicines = []
            e=0
            for i in data:
                if i.startswith("medicineName"):
                    e+=1
                    medicines.append(
                        {
                            "name": data[f"medicineName{e}"],
                            "reason": data[f"medicineReason{e}"],
                            "start": data[f"medicineStart{e}"],
                            "end": data[f"medicineEnd{e}"],
                            "time": data[f"medicineTime{e}"],
                        }
                    )

            for i in range(e):
                data.pop(f"medicineName{str(i+1)}")
                data.pop(f"medicineReason{str(i+1)}")
                data.pop(f"medicineStart{str(i+1)}")
                data.pop(f"medicineEnd{str(i+1)}")
                data.pop(f"medicineTime{str(i+1)}")

            data["medicines"] = medicines
            data["by"] = user["_id"]
            data["on"] = datetime.now().strftime("%d/%m/%Y")
            if patient := database.getUser(data["for"]):
                if patient['_id'] in user["patients"] and user['_id'] in patient["doctors"]:
                    database.addMedicalReport(data)
                    return redirect(url_for('medicalReport'))
            return jsonify({"error": "Patient does not exist"})
    return jsonify({"error": "User is not a doctor"})

@app.route('/reports/medical/<id>', methods=['GET', 'POST'])
def viewMedicalReport(id):
    if 'user' in session:
        user = database.getUser(session['user']['_id'])
        if report := database.getMedicalReport(session['user']['_id'], id):
            if user["type"] == "user":
                return render_template('patients/reports/medical/view.html', user = user, report = report)
            else:
                return render_template('doctors/reports/medical/view.html', user = user, report = report)
        else:
            return redirect(url_for('medicalReport'))
    return redirect(url_for('index'))

@app.route('/reports/lab', methods=['GET'])
def labReport():
    if 'user' not in session:
        return
    user = database.getUser(session['user']['_id'])
    reports = []
    if user["type"] == "user":
        for i in user["labReports"]:
            i['by'] = database.getUser(i['by'])
            reports.append(i)
        return render_template('patients/reports/lab/lab.html', user = user, reports = reports)
    else:
        for i in user["labReports"]:
            i['for'] = database.getUser(i['for'])
            reports.append(i)
        return render_template('doctors/reports/lab/lab.html', user = user, reports = reports)

@app.route('/reports/lab/new', methods=['GET', 'POST'])
def newLabReport():
    if 'user' not in session:
        return redirect(url_for('index'))
    user = database.getUser(session['user']['_id'])
    if user["type"] == "doctor":
        if request.method == 'GET':
            patients = [database.getUser(i) for i in user["patients"]]
            user["patients"] = patients
            return render_template('doctors/reports/lab/add.html', user = user)
        else:
            data = request.form.to_dict()
            data = dict(data)
            Labfile = request.files['Labfile']
            data["by"] = user["_id"]
            data["on"] = datetime.now().strftime("%d/%m/%Y")
            data["fileLink"] = Labfile
            if patient := database.getUser(data["for"]):
                if patient['_id'] in user["patients"] and user['_id'] in patient["doctors"]:
                    database.addLabReport(data)
                    return redirect(url_for('labReport'))
                return jsonify({"error": "Patient does not exist 2"})
            return jsonify({"error": "Patient does not exist 3"})
    return jsonify({"error": "User is not a doctor"})

@app.route('/reports/lab/<id>', methods=['GET', 'POST'])
def viewLabReport(id):
    if 'user' in session:
        user = database.getUser(session['user']['_id'])
        if report := database.getLabReport(session['user']['_id'], id):
            if user["type"] == "user":
                return render_template('patients/reports/lab/view.html', user = user, report = report)
            else:
                return render_template('doctors/reports/lab/view.html', user = user, report = report)
        else:
            return redirect(url_for('medicalReport'))
    return redirect(url_for('index'))

@app.route('/notifications')
def notifs():
    if 'user' in session:
        user = database.getUser(session['user']['_id'])
        if user['type'] == "user":
            notifications = database.getNotifications(user['_id'])
            return render_template('patients/notifications.html', user = user, notifications = notifications)

@app.route('/blogs')
def blogs():
    if 'user' in session:
        user = database.getUser(session['user']['_id'])
        if user['type'] != "doctor":
            return redirect(url_for('index'))
        blogs = database.getBlogs(session['user']['_id'])
        return render_template('blogs/all.html', user = session['user'], blogs = blogs)
    return redirect(url_for('index'))

@app.route('/blogs/new', methods=['GET', 'POST'])
def newBlog():
    if 'user' not in session:
        return redirect(url_for('index'))
    user = database.getUser(session['user']['_id'])
    if user['type'] == "doctor":
        if request.method == 'GET':
            return render_template('blogs/new.html', user = session['user'])
        data = request.form.to_dict()
        data = dict(data)
        data['by'] = session['user']['_id']
        data['on'] = datetime.now().strftime("%d/%m/%Y")
        database.addBlog(data, session['user']['_id'])
        return redirect(url_for('blogs'))
    return redirect(url_for('index'))

@app.route('/blog/<id>')
def viewBlog(id):
    if 'user' in session:
        if blog := database.getBlog(id):
            return render_template('blogs/view.html', user = session['user'], blog = blog)
        return redirect(url_for('blogs'))
    return redirect(url_for('index'))

def handle_authorize(remote, token, user_info):
    if not database.userExists(user_info['email']):
        database.addUser(user_info['email'])
    session['user'] = database.getUserByEmail(user_info['email'])
    return redirect(url_for('index'))

bp = create_flask_blueprint(backends, oauth, handle_authorize)
app.register_blueprint(bp, url_prefix='/')

if __name__ == '__main__':
    app.run(debug=True)
