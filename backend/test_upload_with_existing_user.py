import requests

# Use one of your existing users
# Option 1: chimaobiu@yahoo.com (Verified: True)
# Option 2: cpukka2@gmail.com (Verified: False - needs verification)

# Let's use the verified user
login_data = {
    "username": "chimaobiu@yahoo.com",  # Email as username
    "password": "your-password-here"    # You need to enter the correct password
}

print("Logging in with existing user...")
print(f"Email: {login_data['username']}")
print("Please enter your password if prompted above")

login_response = requests.post(
    "http://localhost:8000/api/auth/login",
    data=login_data
)

if login_response.status_code != 200:
    print(f"Login failed: {login_response.status_code}")
    print(f"Response: {login_response.text}")
    print("\nIf you don't know the password, you can reset it or create a new test user.")
    exit()

token = login_response.json()["access_token"]
print(f"✅ Logged in successfully!\n")

# Create a test video
test_video_content = b"test video content for upload"
files = {
    'file': ('test_video.mp4', test_video_content, 'video/mp4')
}

data = {
    'title': 'Test Upload Video'
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

print(f"Upload status: {upload_response.status_code}")
print(f"Response: {upload_response.text}")

if upload_response.status_code == 200:
    print("\n✅ Upload successful!")
    video_data = upload_response.json()
    print(f"Video ID: {video_data['id']}")
    print(f"Title: {video_data['title']}")
    print(f"Status: {video_data['status']}")
else:
    print("\n❌ Upload failed")
    if upload_response.status_code == 401:
        print("Authentication failed. Token might be invalid.")
    elif upload_response.status_code == 422:
        print("Validation error. Check the request format.")