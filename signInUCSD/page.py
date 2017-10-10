"""
page.py
"""

class Page():
	def __init__(self, title, about):
		self.title = title
		self.about = "<br />".join(about.split("\n"))
		self.forms = []
	
	def setAbout(self, about):
		self.about = "<br />".join(about.split("\n"))
	
	def addForm(self, form):
		self.forms.append(form)

class Form():
	def __init__(self, title, endpoint, submitValue):
		self.title = title
		self.endpoint = endpoint
		self.submit = submitValue
		self.eventUrl = None
		self.inputs = []
		
	def setEventUrl(self, eventUrl):
		self.eventUrl = eventUrl
		
	def addInput(self, title, inputType, inputName, autofocus=None, placeholder=None):
		formInput = {
						"title": title,
						"type": inputType,
						"name": inputName,
						"autofocus": autofocus,
						"placeholder": placeholder
		}
		
		self.inputs.append(formInput)
		
	
	def addTextInput(self, title, inputName, placeholder=None):
		self.addInput(title, "text", inputName,placeholder=placeholder)
	
	def addRadios(self, radioSet):
		self.inputs.append(radioSet)

class RadioSet():
	def __init__(self, categoryTitle, category):
		self.categoryTitle = categoryTitle
		self.category = category
		self.type = "radio"
		self.radios = []
	
	def addRadio(self, title, value):
		radioInput = {
						"title": title,
						"value": value
		}
		
		self.radios.append(radioInput)
		
		

	
		

