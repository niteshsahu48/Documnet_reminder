#!/usr/bin/env python
# coding: utf-8

# In[2]:

from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import ipywidgets as widgets
from IPython.display import display
import os

# Create or load the documents DataFrame
if not os.path.exists('documents.csv'):
    df = pd.DataFrame(columns=['DocumentName', 'UserEmail', 'ExpiryDate', 'RenewalPeriodDays', 'LastAlertSent'])
    df.to_csv('documents.csv', index=False)
else:
    df = pd.read_csv('documents.csv')
    df['ExpiryDate'] = pd.to_datetime(df['ExpiryDate'], errors='coerce')
    if 'LastAlertSent' in df.columns:
        df['LastAlertSent'] = pd.to_datetime(df['LastAlertSent'], errors='coerce')

# Email configuration - NOTE: Use environment variables or a secure config file in production

load_dotenv()
EMAIL_CONFIG = {
    'sender_email': os.getenv("EMAIL_ADDRESS"),
    'sender_password': os.getenv("EMAIL_PASSWORD"),  # Ensure to replace this with a secure way of handling credentials
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587
}

# UI widgets
document_name = widgets.Text(description='Document:')
user_email = widgets.Text(description='Email:')
expiry_date = widgets.DatePicker(description='Expiry Date:')
renewal_period = widgets.IntSlider(description='Alert before (days):', min=1, max=30, value=7)
add_button = widgets.Button(description="Add Document")

check_button = widgets.Button(description="Check for Expiring Documents")
output = widgets.Output()

def add_document(b):
    global df
    with output:
        output.clear_output()

        # Ensure all fields are filled
        if not document_name.value or not user_email.value or not expiry_date.value:
            print("❗ Please fill in all fields.")
            return

        new_row = {
            'DocumentName': document_name.value,
            'UserEmail': user_email.value,
            'ExpiryDate': expiry_date.value,
            'RenewalPeriodDays': renewal_period.value,
            'LastAlertSent': None
        }

        # Append new document data to the DataFrame
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv('documents.csv', index=False)
        print(f"✅ Document '{document_name.value}' added successfully!")

        # Clear input fields
        document_name.value = ''
        user_email.value = ''
        expiry_date.value = None

def send_email_alert(receiver_email, document_name, days_until_expiry, expiry_date):
    try:
        message = MIMEMultipart()
        message['From'] = EMAIL_CONFIG['sender_email']
        message['To'] = receiver_email
        message['Subject'] = f"Renewal Reminder: {document_name}"

        body = f"""
        <html>
            <body>
                <h2>Document Renewal Reminder</h2>
                <p>Your document <strong>{document_name}</strong> is expiring soon!</p>
                <ul>
                    <li>Expiry Date: {expiry_date.strftime('%Y-%m-%d')}</li>
                    <li>Days remaining: {days_until_expiry}</li>
                </ul>
                <p>Please renew this document before it expires.</p>
                <br>
                <p>This is an automated reminder.</p>
            </body>
        </html>
        """

        message.attach(MIMEText(body, 'html'))

        # Send the email via Gmail SMTP
        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
            server.sendmail(EMAIL_CONFIG['sender_email'], receiver_email, message.as_string())

        return True
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False

def check_expiring_documents(b):
    global df
    with output:
        output.clear_output()
        today = datetime.now().date()  # Today's date as a datetime.date object
        alerts_sent = 0

        for index, row in df.iterrows():
            expiry = row['ExpiryDate']
            if pd.isna(expiry):
                continue

            try:
                expiry = pd.to_datetime(expiry)
                expiry_date = expiry.date()
            except Exception as e:
                print(f"❌ Invalid expiry date format in row {index}: {expiry}")
                continue

            days_until_expiry = (expiry_date - today).days
            renewal_period = row['RenewalPeriodDays']

            # Check if alert is due for the document
            if 0 < days_until_expiry <= renewal_period:
                last_alert = row['LastAlertSent'] if pd.notna(row['LastAlertSent']) else None

                if last_alert is None or (datetime.now() - pd.to_datetime(last_alert)).days >= 1:
                    success = send_email_alert(
                        row['UserEmail'],
                        row['DocumentName'],
                        days_until_expiry,
                        expiry_date
                    )

                    if success:
                        df.at[index, 'LastAlertSent'] = datetime.now()
                        alerts_sent += 1
                        print(f"📧 Alert sent for '{row['DocumentName']}' (expiring in {days_until_expiry} days)")

        if alerts_sent == 0:
            print("✅ No documents need alerts at this time.")
        else:
            df.to_csv('documents.csv', index=False)
            print(f"\n✅ Total alerts sent: {alerts_sent}")

# Button actions
add_button.on_click(add_document)
check_button.on_click(check_expiring_documents)

# Display the full UI
display(widgets.VBox([
    widgets.HTML("<h2>Add New Document</h2>"),
    document_name,
    user_email,
    expiry_date,
    renewal_period,
    add_button,
    widgets.HTML("<h2>Check for Expiring Documents</h2>"),
    check_button,
    output
]))


# In[ ]:




