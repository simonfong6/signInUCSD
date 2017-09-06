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
		ucsdId = request.form["ucsdId"]
		print(ucsdId)
		
		ucsdIdNum = ucsdId[2:11]
		print(ucsdIdNum)
		
		ucsdIdInfo = ucsdId.replace(ucsdIdNum, "")
		print(ucsdIdInfo)
		
		ucsdIdInfoHash = bcrypt.hashpw(ucsdIdInfo.encode('utf8'), app.config['UCSDIDINFOSALT'])
		ucsdIdNumHash = bcrypt.hashpw(ucsdIdNum.encode('utf8'), bcrypt.gensalt())
		
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
		db = get_db()
		collection = db.users
		collection.insert_one(newUser)
		
		flash('You have been registered.')
    
	return render_template('register.html', error=error)
	
	
        
if __name__ == "__main__":
	app.run()

