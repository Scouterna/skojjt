class IReport(object):
    """Interface for attendence reports"""
    def __init__(self, dak, semester):
        pass

    def get_url_anme(self):
        """Short name that can be used as a url parameter"""
        pass

    def get_mime_type(self):
        """Mime type for this data format."""
        pass

    def get_filename(self):
        """Returns a filename for this report."""
        pass

    def get_report_string(self):
        """File content data from export."""
        pass
