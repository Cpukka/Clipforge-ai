import requests
import json

# First, login
print("Logging in...")
login_data = {
    "username": "test@example.com",
    "password": "test123"
}

login_response = requests.post(
    "http://localhost:8000/api/auth/login",
    data=login_data
)

if login_response.status_code != 200:
    print(f"Login failed: {login_response.status_code}")
    print(login_response.text)
    exit()

token = login_response.json()["access_token"]
print(f"✅ Logged in successfully\n")

# Create a small test video file (in memory)
test_video_content = b"test video content"
files = {
    'file': ('test_video.mp4', test_video_content, 'video/mp4')
}

data = {
    'title': 'Test Upload'
}

headers = {
    'Authorization': f'Bearer {token}'
}

print("Uploading video...")
upload_response = requests.post(
    "http://localhost:8000/api/videos/upload",
    files=files,
    data=data,
    headers=headers
)

print(f"Status: {upload_response.status_code}")
print(f"Response: {upload_response.text}")

if upload_response.status_code == 200:
    print("\n✅ Upload successful!")
    video_data = upload_response.json()
    print(f"Video ID: {video_data['id']}")
    print(f"Title: {video_data['title']}")
else:
    print("\n❌ Upload failed")