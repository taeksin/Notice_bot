import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from_email = "booogiii12@gmail.com"
password = "pdbksfjyoqrqvwew"
to_email = "yoyo2521@naver.com"
subject = "Your Subject"
message = "Your message goes here."

msg = MIMEMultipart()
msg["From"] = from_email
msg["To"] = to_email
msg["Subject"] = subject
msg.attach(MIMEText(message, "plain"))

server = smtplib.SMTP("smtp.gmail.com", 587)  # Use appropriate SMTP server and port
server.starttls()  # Encrypt the connection
server.login(from_email, password)
server.sendmail(from_email, to_email, msg.as_string())

server.quit()