from celery import Celery
import openai
from app.database import SessionLocal
from app import models

celery = Celery('tasks', broker='redis://redis:6379/0')

@celery.task
def generate_captions(clip_id: int):
    db = SessionLocal()
    try:
        clip = db.query(models.Clip).filter(models.Clip.id == clip_id).first()
        
        # Get transcription for the original video segment
        video = db.query(models.Video).filter(models.Video.id == clip.video_id).first()
        transcription = db.query(models.Transcription).filter(
            models.Transcription.video_id == video.id
        ).first()
        
        if transcription:
            # Extract relevant text segment
            segment_text = extract_segment_text(transcription.segments, clip.start_time, clip.end_time)
            
            # Generate viral caption using OpenAI
            openai.api_key = "your-openai-api-key"
            
            # Generate caption
            caption_response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Generate an engaging social media caption for this video clip"},
                    {"role": "user", "content": segment_text}
                ]
            )
            
            # Generate hashtags
            hashtags_response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Generate 10 relevant hashtags for this video"},
                    {"role": "user", "content": segment_text}
                ]
            )
            
            # Generate title
            title_response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Generate an attention-grabbing title for this video"},
                    {"role": "user", "content": segment_text}
                ]
            )
            
            # Save captions
            caption = models.Caption(
                clip_id=clip_id,
                content=caption_response.choices[0].message.content,
                hashtags=hashtags_response.choices[0].message.content.split(),
                title=title_response.choices[0].message.content
            )
            db.add(caption)
            db.commit()
            
    except Exception as e:
        print(f"Error generating captions: {e}")
    finally:
        db.close()

@celery.task
def export_clip(clip_id: int, platform: str):
    db = SessionLocal()
    try:
        clip = db.query(models.Clip).filter(models.Clip.id == clip_id).first()
        
        # Export logic based on platform
        # This would handle different aspect ratios and formats
        
        clip.views += 1
        db.commit()
        
    except Exception as e:
        print(f"Error exporting clip: {e}")
    finally:
        db.close()

def extract_segment_text(segments, start_time, end_time):
    """Extract text from transcription segments within time range"""
    relevant_text = []
    for segment in segments:
        if segment['start'] >= start_time and segment['end'] <= end_time:
            relevant_text.append(segment['text'])
    return ' '.join(relevant_text)