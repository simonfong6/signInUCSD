"""
signInUCSD.py
"""
# all the imports
import os
import bcrypt
import urllib
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from pymongo import MongoClient
from page import Page, Form, RadioSet
from datetime import datetime

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
        
def redirect_dest(fallback):
    try:
        dest_url = urllib.unquote(request.args.get('next')).decode('utf8')
    except:
        return redirect(fallback)
    return redirect(dest_url)
        
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


        
@app.route('/register', methods=['GET', 'POST'])
def register():
	"""Registers a user to the database."""
	
	registerPage = Page("Register", "")
	
	form = Form("Register", "register", "Register")
	
	form.addTextInput("First Name", "firstName", placeholder="Your first name...")
	form.addTextInput("Last Name", "lastName", placeholder="Your last name...")
	form.addTextInput("UCSD Email", "ucsdEmail", placeholder="Your UCSD email...")
	form.addInput("Password", "password", "password", placeholder="Your password...")
	form.addInput("Confirm Password", "password", "confirmPassword", placeholder="Your password again...")
	form.addTextInput("IEEE Member Number (Enter '0' if you don't have one.):", "ieeeNumber", placeholder="Your IEEE number...")
	
	majors = RadioSet("Major", "major")
	majors.addRadio("Electrical Engineering", "EE")
	majors.addRadio("Computer Engineering", "CE")
	majors.addRadio("Computer Science", "CS")
	majors.addRadio("Mechanical Engineering", "ME")
	
	form.addRadios(majors)
	
	studentType = RadioSet("Student Type", "studentType")
	studentType.addRadio("Non-Transfer (Entered as Freshman)", "nonTransfer")
	studentType.addRadio("Transfer", "transfer")
	studentType.addRadio("Graduate", "graduate")
	
	form.addRadios(studentType)
	
	years = RadioSet("Years", "years")
	years.addRadio("1st Year", "1")
	years.addRadio("2nd Year", "2")
	years.addRadio("3rd Year", "3")
	years.addRadio("4th Year", "4")
	years.addRadio("5th Year", "5")
	years.addRadio("6th Year", "6")
	
	form.addRadios(years)
	
	staffMember = RadioSet("Are you currently an IEEE Staff Member?", "staffMember")
	staffMember.addRadio("Yes", "yes")
	staffMember.addRadio("No", "no")
	
	form.addRadios(staffMember)
	
	registerPage.addForm(form)
	
	error = None
	if request.method == 'POST':
		db = get_db()
		userCol = db.users	
		userFromDb = userCol.find_one({"ucsdEmail" : request.form["ucsdEmail"]})
		
		if(userFromDb):
			flash("You already registered {}! Please continue to log in".format(userFromDb["firstName"]))
			return redirect(url_for('login'))
		else:
			
			passwordHash = None	
			if(request.form["password"] == request.form["confirmPassword"]):
				passwordHash = hashNum(request.form["password"])
			else:
				error="Passwords do not match."
				return render_template('form.html', error=error, page=registerPage)
		
			newUser = {
						"firstName" : request.form["firstName"],
						"lastName" : request.form["lastName"],
						"ucsdEmail" : request.form["ucsdEmail"],
						"password" : passwordHash,
						"admin" : False,
						"ieeeNumber" : request.form["ieeeNumber"],
						"major" : request.form["major"],
						"studentType" : request.form["studentType"],
						"years" : request.form["years"],
						"access" : True,
						"events" : []
			}
		
			userCol.insert_one(newUser)
		
			flash('You have been registered. Please login')
			return redirect(url_for('login'))
	
	return render_template('form.html', error=error, page=registerPage)
	
@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('create_event'))
    
    error = None
    if request.method == 'POST':
        db = get_db()
    	usersCol = db.users
        
        userFromDb = usersCol.find_one({"ucsdEmail":request.form["ucsdEmail"]})
        
        if(not userFromDb):
            flash('Invalid email')
        else:
            password = request.form['password']
            matches = checkNum(password, userFromDb["password"])
        	
            if matches:
                session['logged_in'] = True
                session['admin'] = userFromDb["admin"]
                session['ucsdEmail'] = userFromDb["ucsdEmail"]
                flash('You were logged in')
                return redirect_dest(fallback=url_for('show_users'))
            else:
                flash('Invalid password')
                
   
    loginPage = Page("Login", "")
    
    form = Form("Login", "login", "Login")            
    form.addTextInput("UCSD Email", "ucsdEmail", placeholder="Your UCSD email...")
    form.addInput("Password", "password", "password", placeholder="Your password...")
    
    loginPage.addForm(form)
    
    return render_template('form.html', page=loginPage, redirect_login=request.args.get('next'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('admin', None)
    session.pop('ucsdEmail', None)
    flash('You were logged out')
    return redirect_dest(fallback=url_for('show_users'))

	
@app.route('/users')
def show_users():
	db = get_db()
	usersCol= db.users
	users = usersCol.find({})
	return render_template('show_users.html', users=users)
	
	
@app.route('/users/update', methods=['POST'])
def update_user():
	if (not session.get('logged_in')) or (not session.get('admin')):
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
	if (not session.get('logged_in')) or (not session.get('admin')):
		abort(401)
	db = get_db()
	usersCol= db.users
	userFromDb = usersCol.find_one({"ucsdEmail" : request.form["ucsdEmail"]})
	
	if(userFromDb):
		usersCol.delete_one({"ucsdEmail" : request.form["ucsdEmail"]})
		flash("You have deleted {} {}'s account.".format(userFromDb["firstName"], userFromDb["lastName"]))
	else:
		flash("Your delete attempt has failed because the user in not in the system.")
	
	return redirect(url_for('show_users'))

@app.route('/')
@app.route('/events')
@app.route('/events/create', methods=['GET','POST'])
def create_event():
	db = get_db()
	eventsCol = db.events
	
	if request.method == 'POST':
		if not session.get('admin'):
			abort(401)
		
		event = {
					"title": request.form["title"],
					"officer": request.form["officer"],
					"about": request.form["about"],
					"url": request.form["url"],
					"signups" : [],
					"rsvps" : [],
					"waitlist" : [],
					"signins": [],
					"volunteers": [],
					"participantCount": 0
		}
		
		eventsCol.insert_one(event)
	
	events = eventsCol.find({})
	
	
	return render_template('create_event.html', events=events)
	
@app.route('/events/delete', methods=['POST'])
def delete_event():
	if (not session.get('logged_in')) or (not session.get('admin')):
		abort(401)
	db = get_db()
	eventsCol= db.events
	eventFromDb = eventsCol.find_one({
										"title" : request.form["title"],
										"url" : request.form["url"]
										})
	
	if(eventFromDb):
		eventsCol.delete_one(eventFromDb)
		flash("You have deleted the {} event.".format(eventFromDb["title"]))
	else:
		flash("Your delete attempt has failed because the event was not found.")
	
	return redirect(url_for('create_event'))

@app.route('/events/<eventUrl>')
@app.route('/events/<eventUrl>/dashboard')
def eventSettings(eventUrl):
	db = get_db()
	eventsCol = db.events
	
	event = eventsCol.find_one({"url":eventUrl})
	
	if(event):
		eventPage = Page(event["title"], event["about"])

		return render_template('event_dashboard.html', page=eventPage, eventUrl=event["url"])
	else:
		flash("Event does not exist, you can create one here.")
		return redirect(url_for('create_event'))
		
@app.route('/events/<eventUrl>/signup', methods=["GET", "POST"])
def eventSignup(eventUrl):
	#Check if logged in
	if not session.get('ucsdEmail'):
		return redirect(url_for('login', next=request.endpoint, eventUrl=eventUrl))
	
	db = get_db()
	eventsCol = db.events
	event = eventsCol.find_one({"url":eventUrl})
	
	#Check if there is an event
	if(not event):
		flash("Event does not exist, you can create one here.")
		return redirect(url_for('create_event'))
	
	#Handles sign up request
	if(request.method == "POST"):
		event = {
					"count": 0,
					"url": eventUrl,
					"title": event["title"],
					"status": "signedUp"
		}
		
		usersCol = db.users
		usersCol.update_one(
							{"ucsdEmail": session["ucsdEmail"]},
							{"$push": {
										"events": event
									}
							}
							)
		userFromDb = usersCol.find_one({"ucsdEmail": session["ucsdEmail"]})
							
		user = {
					"firstName": userFromDb["firstName"],
					"lastName": userFromDb["lastName"],
					"ucsdEmail": userFromDb["ucsdEmail"],
					"ieeeNumber": userFromDb["ieeeNumber"],
					"datetime": datetime.utcnow()
		}
		
		eventsCol.update_one(
								{"url":eventUrl},
								{"$push": {
											"signups": user
										}
								}
							)
		flash("You have signed up for {}".format(event["title"]))
		return redirect(url_for('eventSettings', eventUrl=eventUrl))
	
	#Create page	
	signupPage = Page(event["title"], event["about"])
		
	form = Form("Sign Up", "eventSignup", "Sign Up")
	form.setEventUrl(eventUrl)
	
	experience = RadioSet("Experience with Project Space", "experience")
	experience.addRadio("No experience", 1)
	experience.addRadio("Some experience", 2)
	experience.addRadio("Very experienced", 3)
	
	form.addRadios(experience)
	
	signupPage.addForm(form)

	return render_template('form.html', page=signupPage)

@app.route('/events/<eventUrl>/rsvp', methods=['GET','POST'])
def eventRsvp(eventUrl):
	#Check if logged in
	if not session.get('ucsdEmail'):
		return redirect(url_for('login', next=request.endpoint, eventUrl=eventUrl))
	
	db = get_db()
	eventsCol = db.events
	event = eventsCol.find_one({"url":eventUrl})
	
	if(not event):
		flash("Event does not exist, you can create one here.")
		return redirect(url_for('create_event'))
	
	if(request.method == "POST" and request.form["submit"] == "Cancel"):
		flash("You have canceled your acceptance to this event.")
		statusUpdate(eventUrl, "cancels", "canceled")
	
	if(request.method == "POST" and request.form["submit"] == "RSVP"):
		flash("""You have RSVPed to this event. Return here if you need to cancel your RSVP so that
		others may take your spot.""")
		statusUpdate(eventUrl, "rsvps", "rsvped")
	
	#Create page
	rsvpPage = Page(event["title"] + " RSVP", "Please RSVP if you are still going.")
	return render_template("event_rsvp.html", page=rsvpPage, eventUrl=eventUrl)
	
@app.route('/events/<eventUrl>/waitlist', methods=['GET','POST'])
def eventWaitlist(eventUrl):
	#Check if logged in
	if not session.get('ucsdEmail'):
		return redirect(url_for('login', next=request.endpoint, eventUrl=eventUrl))
	
	db = get_db()
	eventsCol = db.events
	event = eventsCol.find_one({"url":eventUrl})
	
	if(not event):
		flash("Event does not exist, you can create one here.")
		return redirect(url_for('create_event'))
	
	if(request.method == "POST" and request.form["submit"] == "Cancel"):
		flash("You have canceled your acceptance to this event.")
		statusUpdate(eventUrl, "cancels", "canceled")
	
	if(request.method == "POST" and request.form["submit"] == "Waitlist"):
		flash("""You have been added to the waitlist for this event. Keep a look out in your emails to see if you have been accepted.""")
		statusUpdate(eventUrl, "waitlists", "waitlisted")
	
	#Create page
	waitlistPage = Page(event["title"] + " Waitlist", "Please click waitlsit if you want to be added to our waitlist for this event.")
	return render_template("event_waitlist.html", page=waitlistPage, eventUrl=eventUrl)

@app.route('/events/<eventUrl>/signin', methods=['GET','POST'])
def eventSignIn(eventUrl):
	db = get_db()
	eventsCol = db.events
	event = eventsCol.find_one({"url":eventUrl})
	
	
	#Event does not exist yet
	if(not event):
		flash("Event does not exist, you can create one here.")
		return redirect(url_for('create_event'))
		
	if request.method == 'POST':
		SALT = "$2b$12$voW9oQb/V53wOs9.YH3br."
		ucsdId = request.form["ucsdId"]
		ucsdIdHash = bcrypt.hashpw(ucsdId.encode('utf8'), SALT)
		
		usersCol = db.users
		
		userFromDb = usersCol.find_one({'ucsdId': ucsdIdHash})
		
		if (userFromDb is None):
			return redirect(url_for('projectSpaceRegistration', ucsdIdHash=ucsdIdHash))
		
		
		eventFromDb = eventsCol.find_one({'url':eventUrl})
					
		user = {
					"firstName": userFromDb["firstName"],
					"lastName": userFromDb["lastName"],
					"ucsdEmail": userFromDb["ucsdEmail"],
					"ieeeNumber": userFromDb["ieeeNumber"],
					"datetime": datetime.utcnow()
		}
	
		eventsCol.update_one(
								{"url": eventUrl}, 
								{
									'$inc': {"participantCount": 1},
									"$push": {
										"signins": user
									}
								}
							)
							
		flash("{}++ \n You are number {}!".format(user['firstName'],int(eventFromDb['participantCount'])+1))
		'''
		usersCol.update_one(
							{
								"ucsdEmail": ucsdEmail,
								"events.url": eventUrl
							},
							{
								"$set": {
											"events.$.status": "signedin"
										}
							}
						)
		
							
		try:
			userFromDb = usersCol.find_one({"ucsdEmail": session["ucsdEmail"]})
						
			user = {
						"firstName": userFromDb["firstName"],
						"lastName": userFromDb["lastName"],
						"ucsdEmail": userFromDb["ucsdEmail"],
						"ieeeNumber": userFromDb["ieeeNumber"],
						"datetime": datetime.utcnow()
			}
		
			eventsCol.update_one(
									{"url": eventUrl}, 
									{
										'$inc': {"participantCount": 1},
										"$push": {
											"signins": user
										}
									}
								)
			flash("Welcome {}, to {}.".format(user["firstName"], event["title"]))
		except (KeyError):
			flash("Unsuccesful sign-in")
		'''
		
	#Create page
	eventPage = Page(event["title"] + " Sign-In", "<h3>Please sign-in by swiping your UCSD ID card.</h3>")
	
	form = Form(event["title"] + " Sign-In", "eventSignIn", "Submit")
	form.setEventUrl(event["url"])
	form.addInput("UCSD ID Card","password" , "ucsdId", autofocus="autofocus", placeholder="UCSD ID Card..." )
	
	eventPage.addForm(form)
		
	return render_template('form.html', page=eventPage)
	
@app.route('/register/projectspace', methods=['GET','POST'])
def projectSpaceRegistration():
	ucsdIdHash = request.args.get('ucsdIdHash').decode('utf8')
	print(ucsdIdHash)
	"""Registers a user to the database."""
	
	registerPage = Page("Register", "")
	
	form = Form("Register", "projectSpaceRegistration", "Register")
	
	form.addTextInput("First Name", "firstName", placeholder="Your first name...")
	form.addTextInput("Last Name", "lastName", placeholder="Your last name...")
	form.addTextInput("UCSD Email", "ucsdEmail", placeholder="Your UCSD email...")
	form.addInput("Password", "password", "password", placeholder="Your password...")
	form.addInput("Confirm Password", "password", "confirmPassword", placeholder="Your password again...")
	form.addTextInput("IEEE Member Number (Enter '0' if you don't have one.):", "ieeeNumber", placeholder="Your IEEE number...")
	
	majors = RadioSet("Major", "major")
	majors.addRadio("Electrical Engineering", "EE")
	majors.addRadio("Computer Engineering", "CE")
	majors.addRadio("Computer Science", "CS")
	majors.addRadio("Mechanical Engineering", "ME")
	
	form.addRadios(majors)
	
	studentType = RadioSet("Student Type", "studentType")
	studentType.addRadio("Non-Transfer (Entered as Freshman)", "nonTransfer")
	studentType.addRadio("Transfer", "transfer")
	studentType.addRadio("Graduate", "graduate")
	
	form.addRadios(studentType)
	
	years = RadioSet("Years", "years")
	years.addRadio("1st Year", "1")
	years.addRadio("2nd Year", "2")
	years.addRadio("3rd Year", "3")
	years.addRadio("4th Year", "4")
	years.addRadio("5th Year", "5")
	years.addRadio("6th Year", "6")
	
	form.addRadios(years)
	
	staffMember = RadioSet("Are you currently an IEEE Staff Member?", "staffMember")
	staffMember.addRadio("Yes", "yes")
	staffMember.addRadio("No", "no")
	
	form.addRadios(staffMember)
	
	registerPage.addForm(form)
	
	error = None
	if request.method == 'POST':
		db = get_db()
		userCol = db.users	
		userFromDb = userCol.find_one({"ucsdEmail" : request.form["ucsdEmail"]})
		
		if(userFromDb):
			flash("You already registered {}! Please continue to sign-in".format(userFromDb["firstName"]))
			return redirect('/events/projectspace1718/signin')
		else:
			
			passwordHash = None	
			if(request.form["password"] == request.form["confirmPassword"]):
				passwordHash = hashNum(request.form["password"])
			else:
				error="Passwords do not match."
				return render_template('form.html', error=error, page=registerPage)
		
			newUser = {
						"firstName" : request.form["firstName"],
						"lastName" : request.form["lastName"],
						"ucsdEmail" : request.form["ucsdEmail"],
						"password" : passwordHash,
						'ucsdId' : ucsdIdHash,
						"admin" : False,
						"ieeeNumber" : request.form["ieeeNumber"],
						"major" : request.form["major"],
						"studentType" : request.form["studentType"],
						"years" : request.form["years"],
						"access" : True,
						"events" : []
			}
		
			userCol.insert_one(newUser)
		
			flash('You have been registered. Please sign-in')
			return redirect('/events/projectspace1718/signin')
	
	return render_template('psForm.html', error=error, page=registerPage, ucsdIdHash=ucsdIdHash)
	
	

#Helper function that updates user status for that event, and updates the event list
#for rsvps, canceled, waitlists, and participants.
def statusUpdate(eventUrl, eventList, newStatus):
	db = get_db()
	
	eventsCol = db.events
	event = eventsCol.find_one({"url":eventUrl})
	
	usersCol = db.users
	usersCol.update_one(
						{
							"ucsdEmail": session["ucsdEmail"],
							"events.url": eventUrl
						},
						{"$set": {
									"events.$.status": newStatus
								}
						}
						)
	userFromDb = usersCol.find_one({"ucsdEmail": session["ucsdEmail"]})
						
	user = {
				"firstName": userFromDb["firstName"],
				"lastName": userFromDb["lastName"],
				"ucsdEmail": userFromDb["ucsdEmail"],
				"ieeeNumber": userFromDb["ieeeNumber"],
				"datetime": datetime.utcnow()
	}
	
	eventsCol.update_one(
							{"url":eventUrl},
							{"$push": {
										eventList: user
									}
							}
						)
	
		
def cardSignIn(eventUrl):
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


        
if(__name__ == "__main__"):
	app.run(host='0.0.0.0', port=5000, threaded=True)

