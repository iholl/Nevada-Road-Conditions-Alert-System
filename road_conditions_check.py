import requests
import pandas as pd
from bs4 import BeautifulSoup

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

from decouple import config

# configure email and password for gmail in .env file
email = config("EMAIL")
password = config("EMAIL_PASSWORD")

# get html table from nv roads and parse tables with pandas
page = requests.get("https://nvroads.com/icx/pages/IncidentList.aspx?listType=Restrictions")
soup = BeautifulSoup(page.content, "html.parser")
table = soup.find_all("table")
initial_tables = pd.read_html(str(table))

# get the road conditions table into df, filter for desired road, reset the index
df = initial_tables[1]
filter_df = df.loc[df[1] == "SR-431"]
final_df = filter_df.drop([0], axis=1)
new_data = final_df.reset_index(drop=True)

# read the current data and compare with the new data
current_data = pd.read_csv("road_conditions.csv", index_col=0)
compare_df = (new_data[3] == current_data["3"])

# log intermediate data
print(new_data)
print(current_data)
print(compare_df)


# sends email with current data table
def send_email():
    # read current dataframe and email recipients (list) to email list of addresses
    df_attachment = pd.read_csv("road_conditions.csv", index_col=0)
    recipients = [email]
    email_list = [elem.strip().split(",") for elem in recipients]

    # start message configuration
    msg = MIMEMultipart()
    msg["Subject"] = "SR-431 Updated Road Conditions"
    msg["From"] = "Nevada Road Conditions Alert System"

    # html for email formatting
    html = """\
    <html>
      <head></head>
      <body>
        {0}
      </body>
    </html>
    """.format(df_attachment.to_html())

    # html to MIMEText and attach to final message
    part1 = MIMEText(html, "html")
    msg.attach(part1)

    # start/connect to server, login with email and password from .env file, send message as email
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(email, password)
    server.sendmail(msg["From"], email_list, msg.as_string())


# if all data in compare dataframe is FALSE update data and send email with new conditions
if compare_df.all():
    print("No updates to the road conditions")
else:
    new_data.to_csv("road_conditions.csv")
    print("New road conditions detected, sending email with new conditions")
    send_email()
    print("Email sent with updated road conditions")
