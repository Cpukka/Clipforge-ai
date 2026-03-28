print("Testing all imports...")

try:
    import aiofiles
    print("✓ aiofiles")
except Exception as e:
    print(f"✗ aiofiles: {e}")

try:
    import boto3
    print("✓ boto3")
except Exception as e:
    print(f"✗ boto3: {e}")

try:
    import ffmpeg
    print("✓ ffmpeg")
except Exception as e:
    print(f"✗ ffmpeg: {e}")

try:
    import whisper
    print("✓ whisper")
except Exception as e:
    print(f"✗ whisper: {e}")

try:
    from fastapi import FastAPI
    print("✓ fastapi")
except Exception as e:
    print(f"✗ fastapi: {e}")

try:
    from sqlalchemy import create_engine
    print("✓ sqlalchemy")
except Exception as e:
    print(f"✗ sqlalchemy: {e}")

print("\nAll imports tested!")