from gaesessions import SessionMiddleware

# suggestion: generate your own random key using os.urandom(64)
# WARNING: Make sure you run os.urandom(64) OFFLINE and copy/paste the output to
# this file.  If you use os.urandom() to *dynamically* generate your key at
# runtime then any existing sessions will become junk every time you start,
# deploy, or update your app!
import os
COOKIE_KEY = '\x05\x82\xddGFU\xd1\xa8\xac\x95\xb12j\xbc\xbd\xdb\xddNy\xd9HI\xe1Ht\xb6\x1a+\x99\x9b*\xcf\xca&F\xc3I\xf4\xfa\xaf\x9a\xffxg\x8a\x086\xaff=\xbf\xab\xfa3\xaf\x99D\x93%\xffh'

def webapp_add_wsgi_middleware(app):
  from google.appengine.ext.appstats import recording
  app = SessionMiddleware(app, cookie_key=COOKIE_KEY)
  app = recording.appstats_wsgi_middleware(app)
  return app
