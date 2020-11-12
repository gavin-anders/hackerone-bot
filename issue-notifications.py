from __future__ import print_function
import slack
import os.path
import base64
import re
import imaplib
import email
from datetime import datetime, timedelta, timezone

USERNAME = os.environ['GMAIL_USERNAME']
PASSWORD = os.environ['GMAIL_PASSWORD']
TOKEN = os.environ['SLACK_API_TOKEN']
LABEL = "HackerOne"
CHANNEL = "#bounty-hunter"

def get_notification_emails():
    mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
    mail.login(USERNAME, PASSWORD)
    mail.select(LABEL)
    rv, data = mail.select(LABEL)
    
    inbox = []
    if rv == "OK":
        rv, data = mail.search(None, "(UNSEEN)")
        for num in data[0].split():
            email_detail = {}
            rv, data = mail.fetch(num, '(RFC822)')
            if rv != 'OK':
                print("ERROR getting message")
                return

            msg = email.message_from_string(data[0][1].decode("utf-8"))
            match = re.search(r"\[.*\]\s\#\d{6}\:", msg['Subject'])
            if match: 
                email_detail['subject'] = msg['Subject']
                email_detail['date'] = msg['Date']
                email_detail['sender'] = msg['From']
                raw = "\n".join(msg.get_payload()[0].as_string().split("\n")[4:])
                email_detail['latest'] = raw
                inbox.append(email_detail)
                mail.uid('STORE', num, '+FLAGS', '(\Seen)')
            else:
                #set the email to be unread
                print("[*] Ignoring {}".format(num))
                mail.uid('STORE', num, '-FLAGS', '(\Seen)')

    mail.logout()
    return inbox

def send_to_slack(subject, date, sender, message, reportid):
    client = slack.WebClient(token=TOKEN)
    block = []
    block.append({
      "type": "section",
      "text": {"type": "mrkdwn","text": "*New HackerOne Notification*"}
    })
    block.append({
      "type": "section",
      "text": {
          "type": "mrkdwn",
          "text": "*Subject:* {}\n*Date:* {}\n*Sender:* {}\n*Report:* https://hackerone.com/bugs?report_id={}".format(subject, date, sender, reportid)
      },
      "accessory": {
          "type": "image",
          "image_url": "https://profile-photos.hackerone-user-content.com/variants/000/000/013/fa942b9b1cbf4faf37482bf68458e1195aab9c02_original.png/eb31823a4cc9f6b6bb4db930ffdf512533928a68a4255fb50a83180281a60da5",
          "alt_text": "h1"
      }
    })
    block.append({
      "type": "context",
      "elements": [
        {
          "type": "mrkdwn",
          "text": "{}".format(message)
        }
      ]
    })
    
    response = client.chat_postMessage(channel=CHANNEL, blocks=block)
    assert response["ok"]

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', dest='test', action='store_true')
    a = parser.parse_args()

    emails = get_notification_emails()
    for email in emails:
        subject = email['subject'].replace("#", "")
        print("[+] {}".format(subject))
        sender = email['sender']
        date = email['date']
        content = email['latest']
        
        try:
            content = content.split("View details on HackerOne")[0]
        except:
            pass
        
        reportid = "n/a"
        try:
            #reportid = subject.split(":")[0].split("] ")[1]
            reportid = re.findall(r"\d{6}", subject)[0]
        except:
            pass
    
        if a.test is False:
            send_to_slack(subject, date, sender, content, reportid)    # subject, date, sender, message, reportid

        print("[+] {}".format(date))
        print("[+] {}".format(sender))
        print("[+] {}".format(reportid))
        print("------------------------")
        print(content)
        print("------------------------")
