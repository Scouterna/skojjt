class IReport():
	def __init__(self, dak, semester):
		pass

	""" Short name that can be used as a url parameter """
	def GetUrlName(self):
		pass

	""" Mime type for this data format """
	def GetMimeType(self):
		pass

	""" File content data from export """
	def GetBinaryStream(self):
		pass
