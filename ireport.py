class IReport:
    """Interface for attendence reports"""
    def __init__(self, dak, semester):
        pass

    def getUrlName(self):
        """Short name that can be used as a url parameter"""
        pass

    def getMimeType(self):
        """Mime type for this data format."""
        pass

    def getFilename(self):
        """Returns a filename for this report."""
        pass

    def getReportString(self):
        """File content data from export."""
        pass
