import whisper
import os
from datetime import datetime

# Load model once
print("Loading Whisper model...")
model = whisper.load_model("base")
print("Model loaded!\n")

# Get all mp4 files
video_files = [f for f in os.listdir("uploads") if f.endswith('.mp4')]

print(f"Found {len(video_files)} videos to transcribe")
print("="*50)

for video_file in video_files:
    video_path = os.path.join("uploads", video_file)
    print(f"\nProcessing: {video_file}")
    print(f"File size: {os.path.getsize(video_path) / 1024 / 1024:.2f} MB")
    
    try:
        start_time = datetime.now()
        result = model.transcribe(video_path)
        end_time = datetime.now()
        
        print(f"✅ Transcription complete in {(end_time - start_time).seconds} seconds")
        print(f"   Language: {result['language']}")
        print(f"   Text length: {len(result['text'])} characters")
        print(f"   Preview: {result['text'][:200]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n" + "="*50)
print("All done!")