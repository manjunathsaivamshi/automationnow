#!/usr/bin/env python3
"""
Efficient YouTube Shorts Video Combiner using FFmpeg
Combines two videos vertically (top 50% + bottom 50%) for YouTube Shorts format
Much faster than MoviePy-based solutions
"""

import os
import subprocess
import json
import argparse

def get_video_info(video_path):
    """
    Get video information using ffprobe
    
    Args:
        video_path (str): Path to video file
        
    Returns:
        dict: Video information including duration, width, height
    """
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_format', '-show_streams', video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        
        # Find video stream
        video_stream = None
        for stream in data['streams']:
            if stream['codec_type'] == 'video':
                video_stream = stream
                break
        
        if not video_stream:
            raise ValueError("No video stream found")
        
        duration = float(data['format']['duration'])
        width = int(video_stream['width'])
        height = int(video_stream['height'])
        
        return {
            'duration': duration,
            'width': width,
            'height': height
        }
        
    except subprocess.CalledProcessError as e:
        raise Exception(f"Failed to get video info: {e}")
    except (KeyError, ValueError) as e:
        raise Exception(f"Failed to parse video info: {e}")

def combine_videos_ffmpeg(video1_path, video2_path, output_path="combined_youtube_short.mp4"):
    """
    Combine two videos vertically using FFmpeg for maximum efficiency
    
    Args:
        video1_path (str): Path to the first video (will be on top)
        video2_path (str): Path to the second video (will be on bottom)
        output_path (str): Output file path
    """
    
    try:
        print("Analyzing videos...")
        
        # Get video information
        info1 = get_video_info(video1_path)
        info2 = get_video_info(video2_path)
        
        print(f"Video 1: {info1['width']}x{info1['height']}, {info1['duration']:.2f}s")
        print(f"Video 2: {info2['width']}x{info2['height']}, {info2['duration']:.2f}s")
        
        # Get minimum duration
        min_duration = min(info1['duration'], info2['duration'])
        print(f"Using duration: {min_duration:.2f} seconds")
        
        # YouTube Shorts dimensions
        target_width = 1080
        target_height = 1920
        half_height = target_height // 2  # 960 pixels each
        
        print("Processing videos with FFmpeg (video_two will be muted)...")
        
        # Build FFmpeg command for efficient processing
        # This command does everything in one pass:
        # 1. Trim both videos to min_duration
        # 2. Scale and crop both videos to fit half the target height
        # 3. Stack them vertically
        # 4. Encode with optimal settings for YouTube
        
        cmd = [
            'ffmpeg', '-y',  # -y to overwrite output file
            
            # Input files
            '-i', video1_path,
            '-i', video2_path,
            
            # Complex filter for processing both videos
            '-filter_complex',
            f'''
            [0:v]scale={target_width}:{half_height}:force_original_aspect_ratio=increase,
            crop={target_width}:{half_height},
            setpts=PTS-STARTPTS[top];
            
            [1:v]scale={target_width}:{half_height}:force_original_aspect_ratio=increase,
            crop={target_width}:{half_height},
            setpts=PTS-STARTPTS[bottom];
            
            [top][bottom]vstack=inputs=2[v]
            ''',
            
            # Map the processed video and only video_one audio
            '-map', '[v]',
            '-map', '0:a',  # Use only audio from video_one (mute video_two)
            
            # Set duration
            '-t', str(min_duration),
            
            # Video encoding settings optimized for YouTube
            '-c:v', 'libx264',
            '-preset', 'medium',  # Balance between speed and quality
            '-crf', '23',  # Good quality
            '-pix_fmt', 'yuv420p',  # Compatibility
            '-r', '30',  # 30 FPS
            
            # Audio encoding
            '-c:a', 'aac',
            '-b:a', '128k',
            '-ar', '44100',
            
            # Output
            output_path
        ]
        
        # Execute FFmpeg command
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print("❌ FFmpeg Error:")
            print(result.stderr)
            return False
        
        print("✅ Video combination completed successfully!")
        print(f"📱 Output video specifications:")
        print(f"   - Resolution: {target_width}x{target_height} (9:16 aspect ratio)")
        print(f"   - Duration: {min_duration:.2f} seconds")
        print(f"   - Audio: Only from video_one (video_two is muted)")
        print(f"   - Format: YouTube Shorts ready")
        print(f"   - File: {output_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error occurred: {str(e)}")
        return False

def check_ffmpeg():
    """Check if FFmpeg is installed and accessible"""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        subprocess.run(['ffprobe', '-version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def main():
    """Main function to handle command line arguments and execute video combination"""
    
    parser = argparse.ArgumentParser(description='Efficiently combine two videos for YouTube Shorts format using FFmpeg')
    parser.add_argument('--video1', default='video_one.mp4', 
                       help='Path to first video file (default: video_one.mp4)')
    parser.add_argument('--video2', default='video_two.mp4', 
                       help='Path to second video file (default: video_two.mp4)')
    parser.add_argument('--output', default='combined_youtube_short.mp4', 
                       help='Output file path (default: combined_youtube_short.mp4)')
    
    args = parser.parse_args()
    
    print("🎬 Efficient YouTube Shorts Video Combiner")
    print("==========================================")
    
    # Check FFmpeg installation
    if not check_ffmpeg():
        print("❌ Error: FFmpeg is not installed or not accessible!")
        print("\nTo install FFmpeg:")
        print("- Windows: Download from https://ffmpeg.org/download.html")
        print("- macOS: brew install ffmpeg")
        print("- Ubuntu/Debian: sudo apt install ffmpeg")
        print("- Other Linux: Check your package manager")
        return
    
    # Check if input files exist
    if not os.path.exists(args.video1):
        print(f"❌ Error: Video file '{args.video1}' not found!")
        print("Make sure the file exists in the current directory.")
        return
    
    if not os.path.exists(args.video2):
        print(f"❌ Error: Video file '{args.video2}' not found!")
        print("Make sure the file exists in the current directory.")
        return
    
    print(f"📂 Input video 1: {args.video1}")
    print(f"📂 Input video 2: {args.video2}")
    print(f"📤 Output video: {args.output}")
    print()
    
    # Combine the videos
    success = combine_videos_ffmpeg(args.video1, args.video2, args.output)
    
    if success:
        print(f"\n🎉 Success! Your YouTube Short is ready: {args.output}")
        print("⚡ Processing was much faster thanks to FFmpeg!")
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # List of filenames to delete
        files_to_delete = ['video_one.mp4', 'video_two.mp4']
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
        print("\n💥 Failed to create the combined video. Please check the error messages above.")

if __name__ == "__main__":
    main()
