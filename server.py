from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from db_setup import Base, User, Employee, Team
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']

engine = create_engine('sqlite:///assets.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

# Functions to help with user credentials

def createUser(login_session):
    newUser = User(name = login_session['username'], email = login_session['email'], picture = login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email = login_session['email']).one()
    return user.id

def getUserInfo(user_id):
    user = session.query(User).filter_by(id = user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email = email).one()
        return user.id
    except:
        return None

# API Endpoints
@app.route('/team/<int:team_id>/JSON/')
def getTeamJSON(team_id):
	team = session.query(Employee).filter_by(team_id = team_id).all()
	return jsonify(Team = [i.serialize for i in team])

@app.route('/team/<int:team_id>/employee/<int:employee_id>/JSON')
def getEmployeeJSON(team_id, employee_id):
	employee = session.query(Employee).filter_by(id = employee_id).one()
	return jsonify(employee = employee.serialize)

@app.route('/team/JSON')
def getTeamsJSON():
	teams = session.query(Team).all()
	return jsonify(teams = [i.serialize for i in teams])

@app.route('/users/JSON')
def getUsersJSON():
	team = session.query(User).all()
	return jsonify(users = [i.serialize for i in team])


# Route for displaying teams / default page
@app.route('/')
@app.route('/teams')
def getRequestDefault():
	manager = session.query(Team)
	if 'username' not in login_session:
		return render_template('publicteams.html', manager = manager)
	else:
		return render_template('teams.html', manager = manager)

# Route for displaying employees on a team
@app.route('/team/<int:team_id>/')
def getTeam(team_id):
	team = session.query(Team).filter_by(id = team_id).one()
	creator = getUserInfo(team.user_id)
	employees = session.query(Employee).filter_by(team_id = team_id).filter_by(level = 0).all()
	if 'username' not in login_session or creator.id != login_session['user_id']:
		return render_template('publicemployees.html', employees = employees, team_id = team_id)
	else:
		return render_template('employees.html', employees = employees, team_id = team_id)

# Route for creating a new team
@app.route('/team/new', methods = ['GET', 'POST'])
def newTeam():
	if 'username' not in login_session:
		return redirect('/login')
 	if request.method == 'POST':
	    newTeam = Team(name = request.form['name'], user_id = login_session['user_id'])
	    session.add(newTeam)
	    flash('New Restaurant %s Successfully Created' % newTeam.name)
	    session.commit()
	    return redirect('/')
	else:
	    return render_template('newTeam.html')

# Route for creating a new employee
@app.route('/team/<int:team_id>/newEmployee', methods = ['GET', 'POST'])
def newEmployee(team_id):
	if 'username' not in login_session:
		return redirect('/login')
	if request.method == 'POST':
		newEmployee = Employee(name = request.form['name'], team_id = team_id, level = 0)
		#user_id = login_session['user_id']
		session.add(newEmployee)
		session.commit()
		return redirect(url_for('getTeam', team_id = team_id))
	else:
		return render_template('newEmployee.html', team_id = team_id)
	return "page to create add a new employee to hierarchy."

# Route for editing a team
@app.route('/team/<int:team_id>/edit', methods = ['GET', 'POST'])
def editTeam(team_id):
	if 'username' not in login_session:
		return redirect('/login')
	editedTeam = session.query(Team).filter_by(id = team_id).one()
	if request.method == 'POST':
		if request.form['name']:
			editedTeam.name = request.form['name']
		session.add(editedTeam)
		session.commit()
		return redirect('/')
	else:
		return render_template('editTeam.html', team_id = team_id, editedTeam = editedTeam)

# Route to edit an employee
@app.route('/team/<int:team_id>/employee/<int:employee_id>/edit', methods = ['GET', 'POST'])
def editEmployee(team_id, employee_id):
	if 'username' not in login_session:
		return redirect('/login')
	editedEmployee = session.query(Employee).filter_by(id = employee_id).one()
	if request.method == 'POST':
		if request.form['name']:
			editedEmployee.name = request.form['name']
		session.add(editedEmployee)
		session.commit()
		return redirect(url_for('getTeam', team_id = team_id))
	else:
		return render_template('editEmployee.html', team_id = team_id, employee_id = employee_id)

# Route to delete a team
@app.route('/team/<int:team_id>/delete', methods = ['GET', 'POST'])
def deleteTeam(team_id):
	if 'username' not in login_session:
		return redirect('/login')
	teamToDelete = session.query(Team).filter_by(id = team_id).one()
	if request.method == 'POST':
		session.delete(teamToDelete)
		session.commit()
		return redirect('/teams')
	else:
		return render_template('deleteTeam.html', team_id = team_id, teamToDelete = teamToDelete)


# Route to delete an existing employee
@app.route('/team/<int:team_id>/employee/<int:employee_id>/delete', methods = ['GET', 'POST'])
def deleteEmployee(team_id, employee_id):
	if 'username' not in login_session:
		return redirect('/login')
	employeeToDelete = session.query(Employee).filter_by(id = employee_id).one()
	if request.method == 'POST':
		session.delete(employeeToDelete)
		session.commit()
		return redirect(url_for('getTeam', team_id = team_id))
	else:
		return render_template('deleteEmployee.html', team_id = team_id, employee_id = employee_id, employeeToDelete = employeeToDelete)

if __name__ == '__main__':
	app.secret_key = 'super_secret_key'
	app.debug = True
	app.run(host='0.0.0.0', port=5000)