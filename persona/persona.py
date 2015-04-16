from flask import Flask, render_template, session, request, abort, g

import requests

import sqlite3
from flask import g

DATABASE = '/home/amulya/portal/flask/examples/persona/outreach-username.db'


app = Flask(__name__)
app.config.update(
    DEBUG=True,
    SECRET_KEY='my development key',
    PERSONA_JS='https://login.persona.org/include.js',
    PERSONA_VERIFIER='https://verifier.login.persona.org/verify',
)
app.config.from_envvar('PERSONA_SETTINGS', silent=True)


@app.before_request
def get_current_user():
    g.user = None
    email = session.get('email')
    if email is not None:
        g.user = email


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
       db = g._database = sqlite3.connect(DATABASE)

    return db

@app.route('/')
def index():
    """Just a generic index page to show."""
    return render_template('index.html')

def query_db(query, args=(), one =False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

@app.route('/_auth/login', methods=['GET', 'POST'])
def login_handler():
    """This is used by the persona.js file to kick off the
    verification securely from the server side.  If all is okay
    the email address is remembered on the server.
    """
    email = query_db('select email from authorize;',one=True)
    #print email
 #   print session['email']
#    if session.get('email') in email:
    resp = requests.post(app.config['PERSONA_VERIFIER'], data={
       'assertion': request.form['assertion'],
       'audience': request.host_url,
    }, verify=True)


    if resp.ok :
        verification_data = resp.json()
       
        if verification_data['status'] == 'okay':
            session['email'] = verification_data['email']
            if session['email'] in email:
                return 'OK'
            abort(400)
        abort(400)
    abort(400)


@app.route('/_auth/logout', methods=['POST'])
def logout_handler():
    """This is what persona.js will call to sign the user
    out again.
    """
    session.clear()
    return 'OK'

if __name__ == '__main__':
    app.run('0.0.0.0')
