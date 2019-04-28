
# automatically generate a htmlform
class HtmlForm():
	fields = [] # list of (fieldname, value, type, description)
	name = ""
	descriptionText = ""
	method="POST"
	submittext=""
	buttonType=""
	disabled=False
	
	def __init__(self, formname, submittext="Spara", method="POST", descriptionText="", buttonType="btn-primary", disabled=False):
		self.fields = []
		self.name = formname
		self.method=method
		self.submittext = submittext
		self.descriptionText = descriptionText
		self.buttonType=buttonType
		self.disabled=disabled
	
	def AddField(self, name, value, description, type="text", required=True):
		self.fields.append((name, value, description, type, required))

	def __str__(self):
		s = ""
		if self.descriptionText != "":
			s += '<p>' + self.descriptionText.replace('\n', '<br/>') + '</p>'
		s += '<form role="form" name="' + self.name + '" method="' + self.method + '" action="./">'
		for field in self.fields:
			s += '<div class="form-group">'
			s += '<label for="' + field[0] + '">' + field[2] + '</label>'
			s += '<input {% if disabled %}disabled="disabled{% endif %} type="' + field[3] + '" class="form-control" size="50" {% if field[4] %}required=""{% endif %} name="' + field[0] + '" id="' + field[0] + '" value="' + str(field[1]) + '"/>'
			s += '</div>'
		s += '<div class="btn-toolbar">'
		s += '<button {% if disabled %}disabled="disabled{% endif %} type="submit" name="submit" class="btn btn-lg ' + self.buttonType +'">' + self.submittext + '</button>'
		s += '</div>'
		s += '</form>'
		return s