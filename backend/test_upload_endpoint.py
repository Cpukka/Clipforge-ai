import requests

# Test if the endpoint exists
response = requests.get("http://localhost:8000/api/videos/")
print(f"GET /api/videos/ status: {response.status_code}")

# Check all available routes
response = requests.get("http://localhost:8000/docs")
print("Check http://localhost:8000/docs for available endpoints")