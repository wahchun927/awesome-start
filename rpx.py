from datetime import datetime
import os
import urllib

try:
    import json
except ImportError:
    from django.utils import simplejson as json

from google.appengine.api import urlfetch
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

from gaesessions import get_current_session

# configure the RPX iframe to work with the server were on (dev or real)
ON_LOCALHOST = ('Development' == os.environ['SERVER_SOFTWARE'][:11])
if ON_LOCALHOST:
    import logging
    if os.environ['SERVER_PORT'] == '80':
        BASE_URL = 'localhost'
    else:
        BASE_URL = 'localhost:%s' % os.environ['SERVER_PORT']
else:
    BASE_URL = 'code-comparison.appspot.com'
LOGIN_IFRAME = '<iframe src="http://gae-sesssions-demo.rpxnow.com/openid/embed?token_url=http%3A%2F%2F' + BASE_URL + '%2Frpx_response" scrolling="no" frameBorder="no" allowtransparency="true" style="width:400px;height:240px"></iframe>'

def redirect_with_msg(h, msg, dst='/'):
    get_current_session()['msg'] = msg
    h.redirect(dst)

# create our own simple users model to track our user's data
class MyUser(db.Model):
    email           = db.EmailProperty()
    display_name    = db.TextProperty()
    past_view_count = db.IntegerProperty(default=0) # just for demo purposes ...

class RPXTokenHandler(webapp.RequestHandler):
    """Receive the POST from RPX with our user's login information."""
    def post(self):
        token = self.request.get('token')
        url = 'https://rpxnow.com/api/v2/auth_info'
        args = {
            'format': 'json',
            'apiKey': 'insert API key here',
            'token': token
        }
        r = urlfetch.fetch(url=url,
                           payload=urllib.urlencode(args),
                           method=urlfetch.POST,
                           headers={'Content-Type':'application/x-www-form-urlencoded'})
        json_data = json.loads(r.content)

        # close any active session the user has since he is trying to login
        session = get_current_session()
        if session.is_active():
            session.terminate()

        if json_data['stat'] == 'ok':
            # extract some useful fields
            info = json_data['profile']
            oid = info['identifier']
            email = info.get('email', '')
            try:
                display_name = info['displayName']
            except KeyError:
                display_name = email.partition('@')[0]

            # get the user's record (ignore TransactionFailedError for the demo)
            user = MyUser.get_or_insert(oid, email=email, display_name=display_name)

            # start a session for the user (old one was terminated)
            session['me'] = user
            session['pvsli'] = 0 # pages viewed since logging in

            redirect_with_msg(self, 'success!')
        else:
            redirect_with_msg(self, 'your login attempt FAILED!')

class GetUser(webapp.RequestHandler):
    def get(self):
        session = get_current_session()
        d = dict()
        if session.has_key('msg'):
            d['login'] = False
            d['msg'] = session['msg']
            del session['msg'] # only show the message once

        if session.has_key('pvsli'):
            d['login'] = True
            session['pvsli'] += 1
            d['user'] = session['me'].key().id_or_name()
            d['name'] = session['me'].display_name
            d['num_now'] = session['pvsli']
            
        callback = self.request.get('callback')
        if callback:
        	content = str(callback) + '(' + json.dumps(d) + ')'
        	return self.response.out.write(content)
    		
        return self.response.out.write(json.dumps(d)) 

class LogoutPage(webapp.RequestHandler):
    def get(self):
        session = get_current_session()
        if session.has_key('me'):
            # update the user's record with total views
            user = session['me']
            user.past_view_count += session['pvsli']
            user.put()
            session.terminate()
            redirect_with_msg(self, 'Logout complete: goodbye ' + user.display_name)
        else:
            redirect_with_msg(self, "How silly, you weren't logged in")

application = webapp.WSGIApplication([('/getuser', GetUser),
                                      ('/logout', LogoutPage),
                                      ('/rpx_response', RPXTokenHandler),
                                     ])

def main(): run_wsgi_app(application)
if __name__ == '__main__': main()
