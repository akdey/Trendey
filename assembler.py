from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, clips_array
import os

class VideoAssembler:
    """Stitches B-Roll and Talking Avatar into a final YouTube video."""
    
    def __init__(self, output_dir="exports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def assemble(self, b_roll_paths, avatar_video_path, audio_path, script_data, final_name="final_video.mp4"):
        print("🧵 Stitching multi-layer video...")
        
        # 1. Load Audio
        audio = AudioFileClip(audio_path)
        
        # 2. Sequence B-Roll
        clips = []
        for path in b_roll_paths:
            clips.append(VideoFileClip(path).without_audio())
        
        # concatenate b-roll to match audio duration
        background = clips[0] # Simplification: use first for now, or concat
        # background = concatenate_videoclips(clips).resize(height=1080)
        background = background.set_duration(audio.duration)
        
        # 3. Process Avatar (Overlay)
        avatar = VideoFileClip(avatar_video_path).resize(height=300) # Small corner size
        
        # 4. Composite Layering
        # Position: Bottom Right (with margin)
        avatar_overlay = avatar.set_position(("right", "bottom")).margin(right=50, bottom=50, opacity=0)
        
        final = CompositeVideoClip([background, avatar_overlay])
        final = final.set_audio(audio)
        
        output_path = os.path.join(self.output_dir, final_name)
        final.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=24)
        
        return output_path
