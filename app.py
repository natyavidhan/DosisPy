from flask import Flask, render_template, request, redirect, url_for, jsonify, session
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
