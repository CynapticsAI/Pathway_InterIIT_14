import requests
import json

headers = {
    'accept': '/',
    'Content-Type': 'application/json',
}

json_data = {
    'query': 'nvidia q3 revenue',
    'k': 6,
}

response = requests.post('http://0.0.0.0:8000/v1/retrieve', headers=headers, json=json_data).text
out = json.loads(response)
for idx, resp in enumerate(out):
    print(f"Output_{idx}================================================================================= \n")
    print(resp['text'])

