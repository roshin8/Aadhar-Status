import requests
import re
from base64 import b64encode
import json
import sys

status_link = 'https://resident.uidai.gov.in/check-aadhaar-status?p_p_id=checkaadhaarstatus_WAR_rpcheckaadhaarstatusportlet&p_p_lifecycle=1&p_p_state=normal&p_p_mode=view&p_p\
		_col_id=column-1&p_p_col_count=1&_checkaadhaarstatus_WAR_rpcheckaadhaarstatusportlet_javax.portlet.action=checkAadharStatus';

WARNING = '\033[93m'
GREEN = '\033[92m'
ENDC = '\033[0m'
ENDPOINT_URL = 'https://vision.googleapis.com/v1/images:annotate'
API_KEY = 'YOUR API KEY'

req = requests.session()

content = req.get("https://resident.uidai.gov.in/check-aadhaar-status", verify=False).content
token_regex = re.compile(r'_checkaadhaarstatus_WAR_rpcheckaadhaarstatusportlet_formDate.*?value=\"(?P<initial_token>\d+)\".*?value=\"(?P<csrf_token>.*?)\"', flags=re.I|re.M|re.S)
captcha_regex = re.compile(r'<img alt=\"Text to Identify\" class=\"captcha\" src=\"(?P<captcha>.*?)\"', flags=re.I|re.M|re.S)


token_match = token_regex.search(content)
initial_token = token_match.group("initial_token")
csrf_token = token_match.group("csrf_token")

captcha_match = captcha_regex.search(content)
captcha_link = captcha_match.group("captcha")
captcha_binary = req.get(captcha_link, verify=False).content

with open('captcha.png', 'w') as f:
	f.write(captcha_binary)



with open('captcha.png', 'rb') as f:
	ctxt = b64encode(f.read()).decode()
	img_requests = {
			'image': {'content': ctxt},
			'features': [{
				'type': 'DOCUMENT_TEXT_DETECTION',
				'maxResults': 2
		}]
	}

image_data = json.dumps({"requests": img_requests }).encode()
response = requests.post(ENDPOINT_URL,
		data=image_data,
		params={'key': API_KEY},
		headers={'Content-Type': 'application/json'})

if response.status_code != 200 or response.json().get('error'):
	print(response.text)
else:
	json_response = response.json()['responses']
	captcha_text = json_response[0]['textAnnotations'][0]['description'].strip()
	if not captcha_text.isdigit():
		print "Please run the program again. Captcha returned alphabets"
		sys.exit(0)

#captcha_text = raw_input("Please enter the Captcha: ")

post_data = {
	'_checkaadhaarstatus_WAR_rpcheckaadhaarstatusportlet_captchaText': captcha_text,
	'_checkaadhaarstatus_WAR_rpcheckaadhaarstatusportlet_formDate': initial_token,
	'csrfToken': csrf_token,
	'dateTime': 'YOUR DATETIME',
	'eid': 'YOUR EID'
}
response = req.post(status_link, data=post_data, verify=False, allow_redirects=True).content

success_message = re.compile(r'<div class="portlet-msg-success">(?P<msg>.*?)</div>', flags=re.I|re.M|re.S)
success_match = re.search(success_message, response)
if success_match:
	print WARNING + success_match.group("msg") + ENDC
else:
	print WARNING + 'Got an other message perhaps' + ENDC

with open('response.html', 'w') as f:
	f.write(response)
