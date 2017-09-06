"""
signInUCSD.py
"""
# all the imports
import os
import bcrypt
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from pymongo import MongoClient

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
        
@app.route('/register', methods=['GET', 'POST'])
def register():
	"""Registers a user to the database."""
	error = None
	if request.method == 'POST':
		db = get_db()
		userCol = db.users
		
		ucsdId = request.form["ucsdId"]
		ucsdIdInfo, ucsdIdNum = toNumAndInfo(request.form["ucsdId"])
		ucsdIdInfoHash = hashInfo(ucsdIdInfo)
		ucsdIdNumHash = hashNum(ucsdIdNum)
		
		userFromDb = userCol.find_one({"ucsdIdInfo" : ucsdIdInfoHash})
		if(userFromDb):
			if(checkNum(ucsdIdNum, userFromDb["ucsdIdNum"])):
				flash("You already registed {}! Please continue to sign-in using your UCSD ID card.".format(userFromDb["firstName"]))
				return redirect(url_for('signin'))
			else:
				flash("Your UCSD ID card information matches another user. Please contact the administrator for assistance.")
				return render_template('register.html', error=error)
		
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
					"access" : access
		}
		
		userCol.insert_one(newUser)
		
		
		flash('You have been registered.')
    
	return render_template('register.html', error=error)

@app.route('/signin', methods=['GET', 'POST'])
def signin():
	"""Checks whether a user is in the database."""
	error = None
	if request.method == 'POST':
		db = get_db()
		usersCol= db.users
		
		ucsdIdInfo, ucsdIdNum = toNumAndInfo(request.form["ucsdId"])
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
			flash('You are not registerd!')
		
		
		
	return render_template('signin.html', error=error)
	
@app.route('/users')
def showUsers():
	db = get_db()
	usersCol= db.users
	
	entries = usersCol.find({})
	return render_template('users.html', entries=entries)
	
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
	
	
	
        
if(__name__ == "__main__"):
	app.run(host='0.0.0.0', port=5000)

