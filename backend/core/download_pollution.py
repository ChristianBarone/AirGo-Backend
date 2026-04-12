import requests, json

url = "https://analisi.transparenciacatalunya.cat/resource/tasf-thgu.json"
data = requests.get(url).json()

with open("pollution.json", "w") as f:
    json.dump(data, f)