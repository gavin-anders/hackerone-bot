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

def get_invite_emails():
    mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
    mail.login(USERNAME, PASSWORD)
    mail.select(LABEL)
    rv, data = mail.select(LABEL)
    
    inbox = []
    if rv == "OK":
        rv, data = mail.search(None, "(UNSEEN)")
        for num in data[0].split():
            detail = {}
            rv, data = mail.fetch(num, '(RFC822)')
            if rv != 'OK':
                print("ERROR getting message")
                return

            msg = email.message_from_string(data[0][1].decode("utf-8"))
            if "invited you to their HackerOne program" in msg['Subject']:
                detail['title'] = msg['Subject']
                raw = "\n".join(msg.get_payload()[0].as_string().split("\n")[4:])
                raw = raw.replace("\n", "").replace("=", "")    #no idea why some of the invites have off characts emdedded 
                r = re.search(r"View invitation \(([^\)]*)", raw)
                if r:
                    print(r.groups())
                    invitelink = r.group(1)
                else:
                    invitelink = "http://hackerone.com/#NoInviteLinkFound"
                detail['invitelink'] = invitelink
                inbox.append(detail)
                mail.uid('STORE', num, '+FLAGS', '(\Seen)')
            else:
                #mark email as unread
                print("[*] Ignoring {}".format(num))
                mail.uid('STORE', num, '-FLAGS', '(\Seen)')


    mail.logout()
    return inbox

def send_to_slack(title, invitelink):
    client = slack.WebClient(token=TOKEN)
    block = []
    block.append({
        "type": "section",
	"text": {
	    "type": "mrkdwn",
	    "text": "{}".format(title)
	},
	"accessory": {
	    "type": "button",
	    "text": {
                "type": "plain_text",
                "emoji": True,
                "text": "Accept"
	    },
           "url": "{}".format(invitelink),
	   "value": "{}".format(invitelink)
	}
    })
    
    response = client.chat_postMessage(channel=CHANNEL, blocks=block)
    assert response["ok"]

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', dest='test', action='store_true')
    a = parser.parse_args()

    emails = get_invite_emails()
    for email in emails:
        if a.test is False:
            send_to_slack(email['title'], email['invitelink'])

        print("[+] {}".format(email['title']))
        print("[+] {}".format(email['invitelink']))
