import os
import json
import random
import yt_dlp
from urllib.parse import urlparse, parse_qs

class YouTubeShortsDownloader:
    def __init__(self):
        self.downloaded_videos_file = "downloaded_videos.json"
        self.downloaded_videos = self.load_downloaded_videos()
        
    def load_downloaded_videos(self):
        """Load the list of previously downloaded video IDs"""
        if os.path.exists(self.downloaded_videos_file):
            try:
                with open(self.downloaded_videos_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_downloaded_videos(self):
        """Save the updated list of downloaded video IDs"""
        with open(self.downloaded_videos_file, 'w') as f:
            json.dump(self.downloaded_videos, f)
    
    def get_ydl_opts(self, for_download=False):
        """Get yt-dlp options with cookies support"""
        base_opts = {
            'quiet': False,
            'no_warnings': False,
        }
        
        # Add cookies if available
        if os.path.exists('cookies.txt'):
            base_opts['cookiefile'] = 'cookies.txt'
            print("Using cookies.txt for authentication")
        
        if for_download:
            base_opts.update({
                'format': 'best[height<=720]',
                'outtmpl': '%(title)s.%(ext)s',
            })
        else:
            base_opts.update({
                'extract_flat': True,
                'playlistend': 100,
            })
        
        return base_opts
    
    def get_random_short_from_channel(self, channel_url, max_attempts=20):
        """Get a random short from a channel without fetching all videos"""
        ydl_opts = self.get_ydl_opts(for_download=False)
        
        try:
            # Clean the channel URL and add /shorts to get only shorts
            clean_url = channel_url.split('?')[0]
            shorts_url = clean_url + "/shorts"
            print(f"Fetching shorts from: {shorts_url}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract shorts directly from the /shorts endpoint
                channel_info = ydl.extract_info(shorts_url, download=False)
                
                if 'entries' not in channel_info or not channel_info['entries']:
                    print("No entries found in channel")
                    return None
                
                print(f"Found {len(channel_info['entries'])} videos")
                
                # All entries from /shorts are already shorts, no need to check duration
                recent_shorts = []
                for entry in channel_info['entries']:
                    if entry and entry.get('id'):
                        # Check if it's already downloaded
                        if entry['id'] not in self.downloaded_videos:
                            recent_shorts.append({
                                'id': entry['id'],
                                'title': entry.get('title', 'Unknown'),
                                'url': f"https://www.youtube.com/watch?v={entry['id']}"
                            })
                
                print(f"Found {len(recent_shorts)} new shorts")
                
                # Return a random short from available ones
                if recent_shorts:
                    return random.choice(recent_shorts)
                    
                return None
                
        except Exception as e:
            print(f"Error getting random short from {channel_url}: {str(e)}")
            return None
    
    def find_random_short(self, channel_urls, max_attempts=10):
        """Find a random short from any of the channels"""
        for attempt in range(max_attempts):
            # Randomly pick a channel
            channel_url = random.choice(channel_urls)
            print(f"Attempt {attempt + 1}: Checking channel: {channel_url}")
            
            # Try to get a random short from this channel
            short_info = self.get_random_short_from_channel(channel_url)
            
            if short_info:
                return short_info
            
            print(f"No new shorts found in this channel, trying another...")
        
        return None
    
    def download_video(self, video_info, output_filename="video_one"):
        """Download a specific video"""
        ydl_opts = self.get_ydl_opts(for_download=True)
        ydl_opts['outtmpl'] = f'{output_filename}.%(ext)s'
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                print(f"Downloading: {video_info['title']}")
                ydl.download([video_info['url']])
                
                # Add to downloaded list
                self.downloaded_videos.append(video_info['id'])
                self.save_downloaded_videos()
                
                print(f"Successfully downloaded: {video_info['title']}")
                return True
                
        except Exception as e:
            print(f"Error downloading video: {str(e)}")
            return False
    
    def download_random_short(self, channel_urls, output_filename="video_one"):
        """Main function to download exactly ONE random short efficiently"""
        print("Starting YouTube Shorts downloader...")
        print("Looking for a random short video...")
        
        # Check if cookies are available
        if os.path.exists('cookies.txt'):
            print("✅ Using cookies for authentication")
        else:
            print("⚠️  No cookies found - may encounter bot detection")
        
        # Find a random short without fetching all videos
        selected_short = self.find_random_short(channel_urls)
        
        if not selected_short:
            print("No new shorts found! Resetting downloaded list and trying again...")
            # Reset and try once more
            self.downloaded_videos = []
            self.save_downloaded_videos()
            selected_short = self.find_random_short(channel_urls)
            
            if not selected_short:
                print("No shorts found in any of the provided channels!")
                return False
        
        print(f"✅ Found random short: {selected_short['title']}")
        
        # Remove existing output file if it exists
        for ext in ['mp4', 'webm', 'mkv', 'avi']:
            if os.path.exists(f"{output_filename}.{ext}"):
                os.remove(f"{output_filename}.{ext}")
                print(f"Removed existing {output_filename}.{ext}")
        
        # Download the selected short (ONLY ONE)
        success = self.download_video(selected_short, output_filename)
        
        if success:
            print(f"✅ Successfully downloaded 1 video saved as: {output_filename}")
            print(f"Total unique videos downloaded so far: {len(self.downloaded_videos)}")
        else:
            print("❌ Failed to download the video")
        
        return success

def main():
    # List of YouTube channel URLs - Fixed missing commas
    channel_urls = [
        "https://youtube.com/@chriswillx",
        "http://www.youtube.com/@premathejournalist",
        "http://www.youtube.com/@jayshetty",  # Added missing comma
        "http://www.youtube.com/@InspirewithNeeraj",
        "http://www.youtube.com/@AadhanTalkies",
        "http://www.youtube.com/@Voiceofmogassala",
        "http://www.youtube.com/@VenuKalyanlifeandbusinesscoach",
        "http://www.youtube.com/@pmfentertainment",
        "http://www.youtube.com/@ManamtvNewsOfficial",
        "http://www.youtube.com/@TeluguConnects_"

        # Add more channel URLs here
        # "https://youtube.com/@anotherchannel",
        # "https://youtube.com/@yetanotherchannel",
    ]
    
    # Create downloader instance
    downloader = YouTubeShortsDownloader()
    
    # Download a random short
    downloader.download_random_short(channel_urls, "video_one")

if __name__ == "__main__":
    main()
