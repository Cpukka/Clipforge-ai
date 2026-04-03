import whisper

# Load model
model = whisper.load_model("base")

# Transcribe your test video
result = model.transcribe("uploads/ba4fa113-005a-4501-8a46-ecaa9852a543.mp4")

print("Transcription complete!")
print(f"Language: {result['language']}")
print(f"Text: {result['text'][:500]}")