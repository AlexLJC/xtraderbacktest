import smtplib
from email.mime.multipart import MIMEMultipart
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
import os
import sys
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest'))
import modules.other.sys_conf_loader as sys_conf_loader

email_conf = sys_conf_loader.get_sys_conf()["notification"]["mail"]


def send_mail(message, subject=None, mail_list=[], file_name=None, cc_list=[]):
    if subject is None:
        subject = "Email Notification"
    emailfrom = email_conf['user']
    password = email_conf['password']
    file_name = file_name
    username = emailfrom
    server = smtplib.SMTP(email_conf['host'], email_conf['port'])
    server.starttls()
    server.login(username, password)
    for mail in mail_list:
        #print("sending to: ", mail)
        emailto = mail
        msg = MIMEMultipart()
        msg["From"] = emailfrom
        msg["To"] = emailto
        if len(cc_list) != 0:
            msg['Cc'] = cc_list[0]
        msg["Subject"] = subject

        body = message
        msg.attach(MIMEText(body, 'plain'))
        if file_name is not None:
            part = MIMEBase("application", 'octet-stream')
            attachment = open(file_name, 'rb')
            part.set_payload((attachment).read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment; filename="%s"' % file_name)
            msg.attach(part)
        text = msg.as_string()
        server.sendmail(emailfrom, emailto, text)
    server.quit()

if __name__ == "__main__":

    send_mail(message = "test message",mail_list = ['lingjiacong07@gmail.com'])