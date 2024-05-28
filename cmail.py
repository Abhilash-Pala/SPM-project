import smtplib
from smtplib import SMTP
from email.message import EmailMessage
def sendmail(to,subject,body):
    server=smtplib.SMTP_SSL('smtp.gmail.com',465)
    server.login('palaabhilash9640@gmail.com','qxue hypn klag eapc')
    msg=EmailMessage()
    msg['FROM']='palaabhilash9640@gmail.com'
    msg['SUBJECT']=subject
    msg['TO']=to
    msg.set_content(body)
    server.send_message(msg) 
    server.quit() 