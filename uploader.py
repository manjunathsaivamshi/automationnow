import os
import pickle
import json
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
import argparse
from datetime import datetime

class YouTubeUploader:
    def __init__(self, credentials_file='credentials.json', token_file='token.pickle'):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.scopes = ['https://www.googleapis.com/auth/youtube.upload']
        self.youtube = None
        self.is_github_actions = os.getenv('GITHUB_ACTIONS') == 'true'
        
    def authenticate(self):
        """Authenticate using existing token (GitHub Actions compatible)"""
        creds = None
        
        # Load existing token (REQUIRED for GitHub Actions)
        if not os.path.exists(self.token_file):
            if self.is_github_actions:
                raise Exception("❌ No token file found in GitHub Actions. Please run local setup first!")
            else:
                raise Exception("❌ No token file found. Please run the local authentication script first.")
        
        try:
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
            print("✅ Loaded existing credentials")
        except Exception as e:
            raise Exception(f"❌ Error loading token file: {e}")
        
        # Handle token refresh (this works in GitHub Actions)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    print("🔄 Refreshing expired credentials...")
                    creds.refresh(Request())
                    print("✅ Credentials refreshed successfully")
                    
                    # Save refreshed credentials
                    with open(self.token_file, 'wb') as token:
                        pickle.dump(creds, token)
                    print("💾 Refreshed credentials saved")
                    
                except Exception as e:
                    if self.is_github_actions:
                        raise Exception(f"❌ Token refresh failed in GitHub Actions: {e}\n"
                                      f"Please generate a new token locally and update GitHub secrets.")
                    else:
                        raise Exception(f"❌ Token refresh failed: {e}\n"
                                      f"Please run the local authentication script again.")
            else:
                if self.is_github_actions:
                    raise Exception("❌ No valid refresh token in GitHub Actions.\n"
                                  "Please generate a fresh token locally and update GitHub secrets.")
                else:
                    raise Exception("❌ No valid refresh token. Please run local authentication script.")
        else:
            print("✅ Using valid existing credentials")
        
        # Build YouTube service
        try:
            self.youtube = build('youtube', 'v3', credentials=creds)
            print("✅ YouTube API service built successfully")
            return True
        except Exception as e:
            raise Exception(f"❌ Failed to build YouTube service: {e}")
    
    def upload_video(self, video_path, title, description="", tags=None, category_id="22", 
                    privacy_status="public", thumbnail_path=None):
        """Upload video to YouTube"""
        if not self.youtube:
            raise Exception("❌ YouTube service not authenticated")
        
        if not os.path.exists(video_path):
            raise Exception(f"❌ Video file not found: {video_path}")
        
        if tags is None:
            tags = ["shorts", "youtube", "video"]
        
        print(f"📤 Uploading video: {video_path}")
        print(f"🎬 Title: {title}")
        print(f"🔒 Privacy: {privacy_status}")
        
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
            print("📊 Upload progress:")
            while response is None:
                try:
                    status, response = request.next_chunk()
                    if status:
                        progress = int(status.progress() * 100)
                        print(f"  📈 {progress}% complete")
                except HttpError as e:
                    if e.resp.status in [500, 502, 503, 504]:
                        print(f"⚠️  Resumable error {e.resp.status}, retrying...")
                        continue
                    else:
                        raise
            
            video_id = response['id']
            print(f"🎉 Video uploaded successfully!")
            print(f"🆔 Video ID: {video_id}")
            print(f"🔗 Video URL: https://www.youtube.com/watch?v={video_id}")
            
            # Upload thumbnail if provided
            if thumbnail_path and os.path.exists(thumbnail_path):
                self.upload_thumbnail(video_id, thumbnail_path)
            
            return video_id
            
        except HttpError as e:
            error_msg = f"HTTP error occurred: {e}"
            if e.resp.status == 401:
                error_msg += "\n🔑 Authentication error - token may have expired"
            elif e.resp.status == 403:
                error_msg += "\n🚫 Permission denied - check YouTube API quotas and permissions"
            elif e.resp.status == 400:
                error_msg += "\n📝 Bad request - check video file and metadata"
            print(f"❌ {error_msg}")
            return None
        except Exception as e:
            print(f"❌ Upload error: {e}")
            return None
    
    def upload_thumbnail(self, video_id, thumbnail_path):
        """Upload custom thumbnail"""
        try:
            print(f"🖼️  Uploading thumbnail: {thumbnail_path}")
            self.youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path)
            ).execute()
            print("✅ Thumbnail uploaded successfully!")
        except Exception as e:
            print(f"❌ Thumbnail upload failed: {e}")

def load_config(config_path='config.json'):
    """Load configuration from JSON file"""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️  Config file {config_path} not found")
        return {}

def main():
    parser = argparse.ArgumentParser(description='Upload video to YouTube (GitHub Actions compatible)')
    parser.add_argument('--title', help='Video title')
    parser.add_argument('--description', help='Video description')
    parser.add_argument('--tags', help='Comma-separated tags')
    parser.add_argument('--thumbnail', help='Path to thumbnail image')
    parser.add_argument('--config', default='config.json', help='Config file path')
    parser.add_argument('--privacy', default='public', choices=['public', 'private', 'unlisted'])
    
    args = parser.parse_args()
    
    # Show environment info
    if os.getenv('GITHUB_ACTIONS') == 'true':
        print("🤖 Running in GitHub Actions")
    else:
        print("💻 Running locally")
    
    # Load config
    config = load_config(args.config)
    
    # Use command line args or config values
    title = args.title or config.get('title', f"Video uploaded on {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    description = args.description or config.get('description', "")
    tags = args.tags.split(',') if args.tags else config.get('tags', ["shorts"])
    
    # Initialize uploader
    uploader = YouTubeUploader()
    
    try:
        print("🚀 Starting YouTube upload process...")
        
        # Authenticate (no interactive auth in GitHub Actions)
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
            print("✅ Upload completed successfully!")
            
            # Cleanup
            script_dir = os.path.dirname(os.path.abspath(__file__))
            files_to_delete = ['combined_youtube_short.mp4']
            
            for filename in files_to_delete:
                file_path = os.path.join(script_dir, filename)
                if os.path.isfile(file_path):
                    try:
                        os.remove(file_path)
                        print(f"🗑️  Deleted: {filename}")
                    except Exception as e:
                        print(f"⚠️  Error deleting {filename}: {e}")
                else:
                    print(f"ℹ️  File not found: {filename}")
        else:
            print("❌ Upload failed!")
            return 1
            
    except Exception as e:
        print(f"💥 Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
