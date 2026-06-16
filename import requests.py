import requests

headers = {"Authorization": "Bearer fapi_HKrjCYppjuontAAKNyFtKhmiCD9ojkfy"}
response = requests.get("https://api.thestatsapi.com/api/football/competitions", headers=headers)
data = response.json()
print(data)