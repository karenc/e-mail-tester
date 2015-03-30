import cgi
import email
from email.header import decode_header
import os

import webapp2
from google.appengine.ext import db
from google.appengine.api import mail

HOSTNAME = os.environ['SERVER_NAME'].replace('appspot', 'appspotmail')

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
                % HOSTNAME)


class MailHandler(webapp2.RequestHandler):
    def post(self, receiver):
        message = mail.InboundEmailMessage(self.request.body)
        try:
            subject = message.subject
        except AttributeError:
            subject = '(No Subject)'
        if subject.startswith('=?'):
            subject = decode_header(subject)[0][0]
        mail = Email(
            address=receiver,
            subject=subject,
            message=message.original.as_string())
        mail.put()


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
        query.filter('address =', '%s@%s' % (address, HOSTNAME))
        query.order('-date')

        self.response.headers['Content-Type'] = 'text/html'
        self.response.out.write(u'''
<html>
    <head>
        <title>Inbox for {}</title>
        <style type="text/css">
            table {{
                border-collapse: collapse;
            }}
            tr:nth-child(even) {{
                background-color: #EEE;
            }}
            th, td {{
                padding: 5px 10px;
            }}
        </style>
    </head>'''.format(address))
        self.response.out.write('<body>\n'
                '<h1>Inbox for %s</title>\n'
                '<table>\n' % address)
        self.response.out.write(
            '<tr>'
            '<th>Delete</th>'
            '<th>Sender</th>'
            '<th>Subject</th></tr>\n')
        for mail_obj in query:
            mail = email.message_from_string(mail_obj.message)
            self.response.out.write(
                u'<tr>'
                u'<td><a href="/delete/{key}">[X]</a></td>'
                u'<td>{sender}</td>'
                u'<td><a href="/message/{key}">{subject}</a></td>'
                u'</tr>'.format(key=mail_obj.key(),
                                sender=cgi.escape(mail.get('From')),
                                subject=cgi.escape(mail_obj.subject)))
        self.response.out.write('</table>\n</body>\n</html>\n')


app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/_ah/mail/(.+)', MailHandler),
    ('/message/(.+)', Message),
    ('/inbox/(.+)', Inbox),
    ('/delete/(.+)', Delete),
    ], debug=True)
