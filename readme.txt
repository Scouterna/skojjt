TODO:
* ancestor queries to get consistency
* reporting
* semesters

Datatables downloaded from configurated as cdn:
https://datatables.net/download/
jquery 1.1
bootstrap
no styling
datatables
fixed columns
fixed header
responsive
scroller


Note:

If running/testing on windows and get this error:
ImportError: cannot import name RAND_egd
edit:
C:\Prgram Files (x86)\Google\google_appengine\google\appengine\dist27\socket.py
remove: RAND_egd from line 73:
from _ssl import RAND_add, RAND_egd, RAND_status, SSL_ERROR_ZERO_RETURN, SSL_ERROR_WANT_READ, SSL_ERROR_WANT_WRITE, SSL_ERROR_WANT_X509_LOOKUP, SSL_ERROR_SYSCALL, SSL_ERROR_SSL, SSL_ERROR_WANT_CONNECT, SSL_ERROR_EOF, SSL_ERROR_INVALID_ERROR_CODE
