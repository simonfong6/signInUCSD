"""
signInUCSD.py
"""
# all the imports
import os
import bcrypt
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from pymongo import MongoClient
from page import Page, Form, RadioSet

#Database key
import dbKey

app = Flask(__name__) # create the application instance :)
app.config.from_object(__name__) # load config from this file , signInUCSD.py

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=dbKey.dbKey,
    SECRET_KEY='development key',
    USERNAME=dbKey.username,
    PASSWORD=dbKey.password,
    UCSDIDINFOSALT=dbKey.ucsdIdInfoSalt
))

def connect_db():
	"""Connects to the signinucsd database on mlab servers."""
	db = MongoClient(app.config['DATABASE'])
	return db
	
def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'dbConnection'):
        g.dbConnection = connect_db()
    return g.dbConnection.signinucsd

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'dbConnection'):
        g.dbConnection.close()
        
def toNumAndInfo(ucsdId):
	ucsdIdNum = ucsdId[2:11]
	ucsdIdInfo = ucsdId.replace(ucsdIdNum, "")
	
	return (ucsdIdInfo,ucsdIdNum)
		
def hashInfo(info):
	return bcrypt.hashpw(info.encode('utf8'), app.config['UCSDIDINFOSALT'])
	
def hashNum(num):
	return bcrypt.hashpw(num.encode('utf8'), bcrypt.gensalt())
	
def checkNum(num, hashedNum):
	return bcrypt.checkpw(num.encode('utf8'), hashedNum.encode('utf8'))
        
@app.route('/admin/register', methods=['GET', 'POST'])
def register_admin():
	if session.get('logged_in'):
		return redirect(url_for('signin'))

	error = None
	if request.method == 'POST':
		db = get_db()
		adminsCol = db.admins
    	
		adminFromDb = adminsCol.find_one({"ucsdEmail":request.form["ucsdEmail"]})

		if(not adminFromDb):
			password = request.form['password']
			pwdhash = hashNum(password)
			newAdmin = {
            			"ucsdEmail": request.form["ucsdEmail"],
            			"password": pwdhash,
            			"firstName": request.form["firstName"],
            			"lastName": request.form["lastName"]
            }
			adminsCol.insert_one(newAdmin)
			flash('Please login using your credentials')
			return redirect(url_for('login'))
		else:
			error = "That email is already registered."
			
	registerPage = Page("Admin Registration", "")
	
	form = Form("Register Admin", "register_admin", "Register")
	form.addTextInput("First Name:", "firstName")
	form.addTextInput("Last Name:", "lastName")
	form.addTextInput("UCSD Email:", "ucsdEmail")
	form.addInput("Password:", "password", "password")
	form.addInput("Confirm Password:", "password", "confirmPassword")
	
	registerPage.addForm(form)
    
	return render_template('form.html', error=error, page=registerPage)

@app.route('/admin/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('signin'))
    
    error = None
    if request.method == 'POST':
        db = get_db()
    	adminsCol = db.admins
        
        adminFromDb = adminsCol.find_one({"ucsdEmail":request.form["ucsdEmail"]})
        
        if(not adminFromDb):
            error = 'Invalid email'
        else:
            password = request.form['password']
            matches = checkNum(password, adminFromDb["password"])
        	
            if matches:
                session['logged_in'] = True
                flash('You were logged in')
                return redirect(url_for('signin'))
            else:
                error = 'Invalid password'
                
   
    loginPage = Page("Login", "")
    
    form = Form("Login", "login", "Login")            
    form.addTextInput("UCSD Email:", "ucsdEmail")
    form.addInput("Password:", "password", "password")
    
    loginPage.addForm(form)
    
    return render_template('form.html', page=loginPage)

@app.route('/admin/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('signin'))
        
@app.route('/register', methods=['GET', 'POST'])
def register():
	"""Registers a user to the database."""
	
	error = None
	if request.method == 'POST':
		db = get_db()
		userCol = db.users
		
		ucsdIdInfo, ucsdIdNum = toNumAndInfo(request.form["ucsdId"])
		ucsdIdInfo += ucsdIdNum[1:4]
		ucsdIdInfoHash = hashInfo(ucsdIdInfo)
		ucsdIdNumHash = hashNum(ucsdIdNum)
		
		userFromDb = userCol.find_one({"ucsdIdInfo" : ucsdIdInfoHash})
		if(userFromDb):
			if(checkNum(ucsdIdNum, userFromDb["ucsdIdNum"])):
				flash("You already registered {}! Please continue to sign-in using your UCSD ID card.".format(userFromDb["firstName"]))
				return redirect(url_for('signin'))
			else:
				flash("Your UCSD ID card information matches another user. Please contact the administrator for assistance.")
		else:
			access = None
			if(request.form["access"] == "true"):
				access = True
			else:
				access = False
		
			newUser = {
						"firstName" : request.form["firstName"],
						"lastName" : request.form["lastName"],
						"ucsdEmail" : request.form["ucsdEmail"],
						"ucsdIdInfo" : ucsdIdInfoHash,
						"ucsdIdNum" : ucsdIdNumHash,
						"access" : access,
						"events" : []
			}
		
			userCol.insert_one(newUser)
		
		
			flash('You have been registered.')
	
	registerPage = Page("Register", "")
	
	form = Form("Register", "register", "Register")
	
	form.addTextInput("First Name:", "firstName")
	form.addTextInput("Last Name:", "lastName")
	form.addTextInput("UCSD Email:", "ucsdEmail")
	form.addTextInput("Access:", "access")
	form.addInput("PID:","password" , "ucsdId")
	
	registerPage.addForm(form)
    
	return render_template('form.html', error=error, page=registerPage)

@app.route('/')
@app.route('/signin', methods=['GET', 'POST'])
def signin():
	"""Checks whether a user is in the database."""
	error = None
	if request.method == 'POST':
		db = get_db()
		usersCol= db.users
		
		ucsdIdInfo, ucsdIdNum = toNumAndInfo(request.form["ucsdId"])
		ucsdIdInfo += ucsdIdNum[1:4]
		ucsdIdInfoHash = hashInfo(ucsdIdInfo)

		
		userFromDb = usersCol.find_one({"ucsdIdInfo" : ucsdIdInfoHash})
		
		if(userFromDb):
			if(checkNum(ucsdIdNum, userFromDb["ucsdIdNum"])):
				if(userFromDb["access"]):
					usersCol.update_one({"ucsdIdInfo" : ucsdIdInfoHash}, {'$inc': {'projectSpace': 1}})
					flash('Access granted!!')
				else:
					flash('Your access has been restricted!')
			else:
				flash('UCSD PID does not match our records. Contact the administrator for help.')
		else:
			flash('You are not registered!')
		
	signInPage = Page("Sign-In", "<h3>Please sign-in using your UCSD ID card.</h3>")
	
	form = Form("Sign-In", "signin", "Submit")
	form.addInput("PID:","password" , "ucsdId",autofocus="autofocus")
	signInPage.addForm(form)
		
	return render_template('form.html', error=error, page=signInPage)
	
@app.route('/users')
def show_users():
	db = get_db()
	usersCol= db.users
	users = usersCol.find({})
	return render_template('show_users.html', users=users)
	
	
@app.route('/users/update', methods=['POST'])
def update_user():
	if not session.get('logged_in'):
		abort(401)
	db = get_db()
	usersCol= db.users
	
	ucsdEmail = request.form["ucsdEmail"]
	
	userFromDb = usersCol.find_one({"ucsdEmail" : ucsdEmail})
	if(userFromDb):
		access = None
		if(request.form["access"] == "true"):
			access = True
		else:
			access = False

		usersCol.update_one({"ucsdEmail" : ucsdEmail}, {"$set":{"access": access}})
		flash("You have updated {} {}'s access level to {}.".format(userFromDb["firstName"], userFromDb["lastName"],access))
	else:
		flash("Your update has failed because the user in not in the system.")
	
	return redirect(url_for('show_users'))

@app.route('/users/delete', methods=['POST'])
def delete_user():
	if not session.get('logged_in'):
		abort(401)
	db = get_db()
	usersCol= db.users
	userFromDb = usersCol.find_one({"ucsdEmail" : request.form["ucsdEmail"]})
	
	if(userFromDb):
		usersCol.delete_one({"ucsdEmail" : ucsdEmail})
		flash("You have deleted {} {}'s account.".format(userFromDb["firstName"], userFromDb["lastName"]))
	else:
		flash("Your delete attempt has failed because the user in not in the system.")
	
	return redirect(url_for('show_users'))

@app.route('/create/event', methods=['GET','POST'])
def create_event():
	if not session.get('logged_in'):
		flash("You must login first.")
		return redirect(url_for('login'))
	
	db = get_db()
	eventsCol = db.events
	
	if request.method == 'POST':
		if not session.get('logged_in'):
			abort(401)
		
		event = {
					"title": request.form["title"],
					"officer": request.form["officer"],
					"url": request.form["url"],
					"participants": [],
					"participantCount": 0
		}
		
		eventsCol.insert_one(event)
	
	events = eventsCol.find({})
	
	return render_template('create_event.html', events=events)

@app.route('/events/<eventUrl>', methods=['GET','POST'])
def eventSignIn(eventUrl):
	db = get_db()
	eventsCol = db.events
	
	event = eventsCol.find_one({"url":eventUrl})
	
	if request.method == 'POST':
		db = get_db()
		usersCol= db.users
		
		ucsdIdInfo, ucsdIdNum = toNumAndInfo(request.form["ucsdId"])
		ucsdIdInfo += ucsdIdNum[1:4]
		ucsdIdInfoHash = hashInfo(ucsdIdInfo)

		
		userFromDb = usersCol.find_one({"ucsdIdInfo" : ucsdIdInfoHash})
		
		if(userFromDb):
			if(checkNum(ucsdIdNum, userFromDb["ucsdIdNum"])):
				if(userFromDb["access"]):
					if(not usersCol.find_one({"ucsdIdInfo" : ucsdIdInfoHash, "events.url": event["url"] })):
						usersCol.update_one({"ucsdIdInfo" : ucsdIdInfoHash}, {'$push': {"events":{"title": event["title"], "count": 1, "url":event["url"]}}})
					else:
						usersCol.update_one({"ucsdIdInfo" : ucsdIdInfoHash, "events.url": event["url"] },
					 	{'$inc': {"events.$.count": 1}})
					eventsCol.update_one({"url":eventUrl}, 
										{'$inc':{"participantCount": 1},})
					flash('Access granted!!')
				else:
					flash('Your access has been restricted!')
			else:
				flash('UCSD PID does not match our records. Contact the administrator for help.')
		else:
			flash('You are not registered!')
		return redirect(url_for('eventSignIn', eventUrl=event["url"]))
	
	
	if(event):
		eventPage = Page(event["title"] + " Sign-In", "<h3>Please sign-in using your UCSD ID card.</h3>")
		form = Form(event["title"] + " Sign-In", "eventSignIn", "Submit")
		form.setEventUrl(event["url"])
		form.addInput("PID:","password" , "ucsdId",autofocus="autofocus")
		eventPage.addForm(form)
		
		return render_template('form.html', page=eventPage)
	else:
		flash("Event does not exist, you can create one here.")
		return redirect(url_for('create_event'))

	
		
@app.route('/general/register', methods=['GET','POST'])
def register_general():
	
	about = """
All engineers need some computer skills, and we are not talking about "This is a keyboard, and that is the Ethernet cable"

Come and learn some C Programming along with UNIX, vim, and git! Experience some software development in the real world!

This workshop is proudly brought you by the UC San Diego chapters of IEEE, Eta Kappa Nu, and Tau Beta Pi!

Date & Time: Jan. 22 (Sunday, Week 2) 10am-12:30pm
Location: T.B.A.

Questions? Please contact us at IEEE.UCSD.Tech@gmail.com"""
	
	registerPage = Page("Arduino Workshop", about)
	
	form = Form("Arduino Workshop", "register_general", "Register")
	form.addTextInput("First Name:", "firstName")
	form.addTextInput("Last Name:", "lastName")
	form.addTextInput("UCSD Email:", "ucsdEmail")
	form.addTextInput("IEEE Member Number (Enter '0' if you don't have one.):", "ieeeNumber")
	
	majors = RadioSet("Major:", "major")
	majors.addRadio("Electrical Engineering", "EE")
	majors.addRadio("Computer Engineering", "CE")
	majors.addRadio("Computer Science", "CS")
	majors.addRadio("Mechanical Engineering", "ME")
	
	form.addRadios(majors)
	
	studentType = RadioSet("Student Type:", "studentType")
	studentType.addRadio("Non-Transfer (Entered as Freshman)", "nonTransfer")
	studentType.addRadio("Transfer", "transfer")
	studentType.addRadio("Graduate", "graduate")
	
	form.addRadios(studentType)
	
	years = RadioSet("Years:", "years")
	years.addRadio("1st Year", "1")
	years.addRadio("2nd Year", "2")
	years.addRadio("3rd Year", "3")
	years.addRadio("4th Year", "4")
	years.addRadio("5th Year", "5")
	years.addRadio("6th Year", "6")
	
	form.addRadios(years)
	
	staffMember = RadioSet("Are you currently an IEEE Staff Member?:", "staffMember")
	staffMember.addRadio("Yes", "yes")
	staffMember.addRadio("No", "no")
	
	form.addRadios(staffMember)
	
	registerPage.addForm(form)
	
	
	if(request.method == "POST"):
		for key in request.form:
			print(key,request.form[key])
	
	
	return render_template('form.html', page=registerPage)

        
if(__name__ == "__main__"):
	app.run(host='0.0.0.0', port=5000)

