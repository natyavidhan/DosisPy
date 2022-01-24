from flask import Flask, render_template, request, redirect, url_for, jsonify, session, abort
from models import Database
from authlib.integrations.flask_client import OAuth
from loginpass import create_flask_blueprint, GitHub, Google, Gitlab, Discord
from dotenv import dotenv_values

app = Flask(__name__)
oauth = OAuth(app)

config = dotenv_values(".env")
config = dict(config)

app.secret_key = config["SECRET_KEY"]
for keys in config.keys():
    app.config[keys] = config[keys]
    
database = Database()
backends = [GitHub, Google, Gitlab, Discord]

@app.route('/')
def index():
    if 'user' in session:
        user = database.getUser(session['user']['_id'])
        if user["type"] == "doctor":
            return render_template('doctor.html', user = user)
        return render_template('user.html', user = user)
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
            for keys in data.keys():
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
    if 'user' in session:
        if request.method == 'GET':
            user = database.getUser(session['user']['_id'])
            if user["type"] == "user":
                doctorIDs = user["doctors"]
                doctors = []
                for d in doctorIDs:
                    doctors.append(database.getUser(d))
                return render_template('doctors.html', doctors = doctors, user = user)
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
                        return redirect(url_for('doctors'))
                else:
                    return jsonify({"error": "User is not a doctor"})
            else:
                return jsonify({"error": "User does not exist"})
        elif request.method == 'DELETE':
            doctorId = request.form.get("doctorId")
            doc = database.getUser(doctorId)
            user = database.getUser(session['user']['_id'])
            if doc:
                if doc["type"] == "doctor":
                    if doc["_id"] in user["doctors"]:
                        database.removeDoctor(session['user']['_id'], doctorId)
            return jsonify({"success": "Doctor removed"})

@app.route('/patients', methods=['GET', 'POST', 'DELETE'])
def patients():
    if 'user' in session:
        if request.method == 'GET':
            user = database.getUser(session['user']['_id'])
            if user["type"] == "doctor":
                patientsIDs = user["patients"]
                patients = []
                for d in patientsIDs:
                    patients.append(database.getUser(d))
                return render_template('patients.html', patients = patients, user = user)
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
                        return redirect(url_for('patients'))
                else:
                    return jsonify({"error": "User is not a patient"})
            else:
                return jsonify({"error": "User does not exist"})
        elif request.method == 'DELETE':
            patientId = request.form.get("patientId")
            patient = database.getUser(patientId)
            user = database.getUser(session['user']['_id'])
            if doc:
                if patient["type"] == "user":
                    if patient["_id"] in user["patients"]:
                        database.removeDoctor(session['user']['_id'], patientId)
            return jsonify({"success": "Patient removed"})

@app.route('/doctor/<id>')
def doctorView(id):
    if 'user' in session:
        user = database.getUser(session['user']['_id'])
        if user["type"] == "user":
            doctor = database.getUser(id)
            return render_template('doctorview.html', user = user, doctor = doctor)
        
def handle_authorize(remote, token, user_info):
    if database.userExists(user_info['email']):
        session['user'] = database.getUserByEmail(user_info['email'])
    else:
        database.addUser(user_info['email'])
        session['user'] = database.getUserByEmail(user_info['email'])
    return redirect(url_for('index'))

bp = create_flask_blueprint(backends, oauth, handle_authorize)
app.register_blueprint(bp, url_prefix='/')

if __name__ == '__main__':
    app.run(debug=True)
