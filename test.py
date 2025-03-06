import requests

API_TOKEN = "8129915927:AAFCGGw07JkeWlUrqBsKzsU1IXPwQXT-n8Y"
url = f"https://api.telegram.org/bot{API_TOKEN}/getMe"

print('response 1')
try:
    response = requests.get(url)
    print('response ')
    print(response.json())
except Exception as e:
    print(f"Error: {e}")
