import os
import slack
import requests
import pprint
from datetime import datetime

token=os.environ['SLACK_API_TOKEN']
assert token is not None

channel = "#bounty-hunter"
client = slack.WebClient(token=token)

#get feed
url = "https://hackerone.com:443/graphql?"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0", "Content-Type": "application/json", "Connection": "close"}
body = {"query": "query Hacktivity_page_QueryRelayQL($id_0:ID!,$first_1:Int!,$secure_order_by_2:FiltersHacktivityItemFilterOrder!,$where_3:FiltersHacktivityItemFilterInput!,$size_5:ProfilePictureSizes!,$size_6:ProfilePictureSizes!) {node(id:$id_0) {...Fe}} fragment F0 on HacktivityItemInterface {__typename} fragment F1 on HacktivityItemInterface {votes {total_count},upvoted_by_current_user,__typename,...F0} fragment F2 on Team {_profile_picture:profile_picture(size:$size_6),name,about,currency} fragment F3 on Team {handle,name,...F2} fragment F4 on Undisclosed {reporter {username},team {handle,name,url,...F3},latest_disclosable_action,latest_disclosable_activity_at,requires_view_privilege,total_awarded_amount,currency} fragment F5 on Undisclosed {...F4} fragment F6 on Disclosed {id,reporter {username},team {handle,name,url,...F3},report {title,substate,url,id},latest_disclosable_action,latest_disclosable_activity_at,total_awarded_amount,severity_rating,currency} fragment F7 on Disclosed {...F6} fragment F8 on HackerPublished {id,reporter {username},team {handle,name,_profile_picture:profile_picture(size:$size_5),url,...F3},report {url,title,substate},latest_disclosable_activity_at,severity_rating} fragment F9 on HackerPublished {...F8} fragment Fa on Node {__typename} fragment Fb on HacktivityItemUnion {__typename,...F1,...F5,...F7,...F9,...Fa} fragment Fc on HacktivityItemInterface {id,__typename,...Fb} fragment Fd on HacktivityItemConnection {total_count,edges {cursor,node {__typename,...Fc,...Fa}}} fragment Fe on Query {_hacktivity_items:hacktivity_items(first:$first_1,query:\"\",secure_order_by:$secure_order_by_2,where:$where_3) {total_count,...Fd},id}", "variables": {"first_1": 25, "id_0": "Z2lkOi8vaGFja2Vyb25lL09iamVjdHM6OlF1ZXJ5L3N0YXRpYw==", "last_4": 10, "secure_order_by_2": {"latest_disclosable_activity_at": {"_direction": "DESC"}}, "size_5": "medium", "size_6": "small", "where_3": {"report": {"disclosed_at": {"_is_null": False}}}}}
resp = requests.post(url, headers=headers, json=body)
content = resp.json()

#parse issues
issues = []
for e in content["data"]["node"]["_hacktivity_items"]["edges"]:
    node = e["node"]
    if node["__typename"] == "Disclosed":
        #check if in the last 24 hours 2019-09-09T16:50:18.011Z
        dtobj = datetime.strptime(node["latest_disclosable_activity_at"], '%Y-%m-%dT%H:%M:%S.%fZ')
        diff = datetime.utcnow() - dtobj
        if diff.days == 0:
            vendor = node["team"]["handle"]
            image = node["team"]["_profile_picture"]
            title = node["report"]["title"]
            link = node["report"]["url"]
            bounty = "{} {}".format(node["total_awarded_amount"], node["currency"])
            severity = node["severity_rating"]
            foundby = node["reporter"]["username"]
            issues.append({"link":link, "title": title, "foundby": foundby, "vendor": vendor, "bounty": bounty, "severity": severity, "image": image})

#create slack blocks
block_message = []
block_message.append(
    {
		"type": "section",
		"text": {
			"type": "plain_text",
			"emoji": True,
			"text": "Latest HackerOne bugs"
		}
	}
)
block_message.append(
    {
		"type": "divider"
	}
)

for i in issues:
    print(i)
    text = "*<{link}|{title}>*\nReported by {foundby} to {vendor}  |  {bounty}  |  {risk}".format(link=i["link"], 
                                                                                title=i["title"], 
                                                                                foundby=i["foundby"], 
                                                                                vendor=i["vendor"], 
                                                                                bounty=i["bounty"],
                                                                                risk=i["severity"])
    block_message.append(
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text
            },
            "accessory": {
                "type": "image",
                "image_url": "{}".format(i["image"]),
                "alt_text": "NO IMAGE HERE"
            }
        }
    )

block_message.append(
    {
		"type": "section",
		"text": {
			"type": "mrkdwn",
			"text": "*<https://hackerone.com/hacktivity?order_direction=DESC&order_field=latest_disclosable_activity_at&filter=type%3Apublic|Go to hacktivity feed>*"
	}
        }
)

#post to slack
response = client.chat_postMessage( channel=channel, blocks=block_message)
assert response["ok"]
