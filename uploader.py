import os
import pickle
import json
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import argparse
from datetime import datetime

class YouTubeUploader:
    def __init__(self, credentials_file='credentials.json', token_file='token.pickle'):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.scopes = ['https://www.googleapis.com/auth/youtube.upload']
        self.youtube = None
        
    def authenticate(self):
        """Authenticate and build YouTube service"""
        creds = None
        
        # Load existing token
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # If there are no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.scopes)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        self.youtube = build('youtube', 'v3', credentials=creds)
        return True
    
    def upload_video(self, video_path, title, description="", tags=None, category_id="22", 
                    privacy_status="public", thumbnail_path=None):
        """Upload video to YouTube"""
        if not self.youtube:
            raise Exception("YouTube service not authenticated")
        
        if tags is None:
            tags = ["shorts", "youtube", "video"]
        
        # Video metadata
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags,
                'categoryId': category_id
            },
            'status': {
                'privacyStatus': privacy_status,
                'selfDeclaredMadeForKids': False
            }
        }
        
        # Media upload
        media = MediaFileUpload(
            video_path,
            chunksize=-1,
            resumable=True,
            mimetype='video/*'
        )
        
        try:
            # Execute upload
            request = self.youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    print(f"Upload progress: {int(status.progress() * 100)}%")
            
            video_id = response['id']
            print(f"Video uploaded successfully! Video ID: {video_id}")
            print(f"Video URL: https://www.youtube.com/watch?v={video_id}")
            
            # Upload thumbnail if provided
            if thumbnail_path and os.path.exists(thumbnail_path):
                self.upload_thumbnail(video_id, thumbnail_path)
            
            return video_id
            
        except HttpError as e:
            print(f"An HTTP error occurred: {e}")
            return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None
    
    def upload_thumbnail(self, video_id, thumbnail_path):
        """Upload custom thumbnail"""
        try:
            self.youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path)
            ).execute()
            print("Thumbnail uploaded successfully!")
        except Exception as e:
            print(f"Thumbnail upload failed: {e}")

def load_config(config_path='config.json'):
    """Load configuration from JSON file"""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Config file {config_path} not found")
        return {}

def main():
    parser = argparse.ArgumentParser(description='Upload video to YouTube')
    parser.add_argument('--title', help='Video title')
    parser.add_argument('--description', help='Video description')
    parser.add_argument('--tags', help='Comma-separated tags')
    parser.add_argument('--thumbnail', help='Path to thumbnail image')
    parser.add_argument('--config', default='config.json', help='Config file path')
    parser.add_argument('--privacy', default='public', choices=['public', 'private', 'unlisted'])
    
    args = parser.parse_args()
    
    # Load config
    config = load_config(args.config)
    
    # Use command line args or config values
    title = args.title or config.get('title', f"Video uploaded on {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    description = args.description or config.get('description', "")
    tags = args.tags.split(',') if args.tags else config.get('tags', ["shorts"])
    
    # Initialize uploader
    uploader = YouTubeUploader()
    
    try:
        # Authenticate
        uploader.authenticate()
        
        # Upload video
        video_id = uploader.upload_video(
            video_path='combined_youtube_short.mp4',
            title=title,
            description=description,
            tags=tags,
            privacy_status=args.privacy,
            thumbnail_path=args.thumbnail
        )
        
        if video_id:
            print("Upload completed successfully!")
            script_dir = os.path.dirname(os.path.abspath(__file__))

            # List of filenames to delete
            files_to_delete = ['combined_youtube_short.mp4']
            for filename in files_to_delete:
                file_path = os.path.join(script_dir, filename)
                if os.path.isfile(file_path):
                    try:
                        os.remove(file_path)
                        print(f"Deleted: {filename}")
                    except Exception as e:
                        print(f"Error deleting {filename}: {e}")
                else:
                    print(f"File not found: {filename}")
        else:
            print("Upload failed!")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
