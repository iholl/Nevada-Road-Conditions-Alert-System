import requests
import pandas as pd
from bs4 import BeautifulSoup

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

from decouple import config

page = requests.get("https://nvroads.com/icx/pages/IncidentList.aspx?listType=Restrictions")
soup = BeautifulSoup(page.content, "html.parser")
table = soup.find_all("table")
initial_tables = pd.read_html(str(table))

df = initial_tables[1]
filter_df = df.loc[df[1] == "SR-431"]
final_df = filter_df.drop([0], axis=1)
new_data = final_df.reset_index(drop=True)

current_data = pd.read_csv("road_conditions.csv", index_col=0)
compare_df = (new_data[3] == current_data["3"])

email = config("EMAIL")
password = config("EMAIL_PASSWORD")

if compare_df.all():
    print("No updates to the road conditions")
else:
    # email
    new_data.to_csv("road_conditions.csv")
    df_test = pd.read_csv("road_conditions.csv", index_col=0)
    recipients = [email]
    email_list = [elem.strip().split(",") for elem in recipients]
    msg = MIMEMultipart()
    msg["Subject"] = "SR-431 Updated Road Conditions"
    msg["From"] = email

    html = """\
    <html>
      <head></head>
      <body>
        {0}
      </body>
    </html>
    """.format(df_test.to_html())

    part1 = MIMEText(html, "html")
    msg.attach(part1)
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(email, password)
    server.sendmail(msg["From"], email_list, msg.as_string())
    # text
    sms_gateway = config("PHONE_NUMBER")
    smtp = "smtp.gmail.com"
    port = 587
    server = smtplib.SMTP(smtp, port)
    server.starttls()
    server.login(email, password)
    msg = MIMEMultipart()
    msg['From'] = email
    msg['To'] = sms_gateway
    msg['Subject'] = "SR-431 Conditions Update"
    body = "Conditions have changed check your email for details!"
    msg.attach(MIMEText(body, 'plain'))
    sms = msg.as_string()
    server.sendmail(email, sms_gateway, sms)
    server.quit()

    print("Text and email sent with updated road conditions")
