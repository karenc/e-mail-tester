import os

import webapp2
from google.appengine.ext import db
from google.appengine.api import mail

class Email(db.Model):
    date = db.DateTimeProperty(auto_now_add=True)
    address = db.StringProperty()
    subject = db.TextProperty()
    message = db.TextProperty()


class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write('Welcome to E-mail Tester!\n\n'
                'You can send emails to anything@%s\n\n'
                'You can check your inbox at /inbox/anything\n'
                'Check your message at /message/msgkey\n'
                'Delete your message at /delete/msgkey\n'
                % os.environ['SERVER_NAME'])


class MailHandler(webapp2.RequestHandler):
    def post(self, receiver):
        message = mail.InboundEmailMessage(self.request.body)
        email = Email(
                address=receiver,
                subject=message.subject,
                message=message.original.as_string())
        email.put()


class Message(webapp2.RequestHandler):
    def get(self, msgkey):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write(Email.get(msgkey).message)


class Delete(webapp2.RequestHandler):
    def get(self, msgkey):
        Email.get(msgkey).delete()
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write('Email Deleted')


class Inbox(webapp2.RequestHandler):
    def get(self, address):
        query = db.Query(Email)
        query.filter('address =', '%s@%s' % (address,
            os.environ['SERVER_NAME']))
        query.order('-date')

        self.response.headers['Content-Type'] = 'text/html'
        self.response.out.write('<html><head>\n'
                '<title>Inbox for %s</title>\n'
                '</head>\n' % address)
        self.response.out.write('<body>\n'
                '<h1>Inbox for %s</title>\n'
                '<table>\n' % address)
        self.response.out.write('<tr><th>Subject</th></tr>\n')
        for email in query:
            self.response.out.write('<tr><td><a href="/message/%s">%s</a></td>'
                    '</tr>' % (email.key(), email.subject))
        self.response.out.write('</table>\n</body>\n</html>\n')


app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/_ah/mail/(.+)', MailHandler),
    ('/message/(.+)', Message),
    ('/inbox/(.+)', Inbox),
    ('/delete/(.+)', Delete),
    ], debug=True)
