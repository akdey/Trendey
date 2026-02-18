import os
import time
import json
from engine import ScriptEngine, RemoteAssetEngine, AudioEngine
from assembler import VideoAssembler

class TrendeyOrchestrator:
    """The Main Agent that runs the entire pipeline from Topic to MP4."""
    
    def __init__(self):
        # Configuration - Load from Environment or Config
        from dotenv import load_dotenv
        load_dotenv()
        
        self.hf_token = os.getenv("HF_TOKEN")
        self.video_space = os.getenv("VIDEO_BACKEND", "Wan-AI/Wan2.1-T2V-14B")
        self.lipsync_space = os.getenv("AVATAR_BACKEND", "KwaiVGI/LivePortrait")
        self.avatar_ref = "assets/avatar_ref.jpg"
        
        # Hardcoded High-CPM Topics for 2026
        self.default_topics = [
            "The Rise of Agentic AI: How 2026 Shifted Everything",
            "Quantum Smartphones: Real or Hype?",
            "How to Build a $1M Portfolio with AI Agents",
            "Future of Work: The 3-Day Week is Here",
        ]
        
        # Initialize Engines
        self.script_engine = ScriptEngine(self.hf_token)
        self.asset_engine = RemoteAssetEngine(self.video_space, self.lipsync_space)
        self.audio_engine = AudioEngine()
        self.assembler = VideoAssembler()

    def run(self, manual_topic=None):
        print("🚀 Starting Viral Video Pipeline...")
        
        # Check for avatar image
        if not os.path.exists(self.avatar_ref):
            print(f"❌ Error: Avatar reference photo not found at {self.avatar_ref}")
            print("Please save your photo to 'assets/avatar_ref.jpg' before running.")
            return None

        # Step 1: Topic Selection
        topic = manual_topic or random.choice(self.default_topics)
        print(f"📌 Chosen Topic: {topic}")
        
        # Step 2: Scripting
        script = self.script_engine.generate_full_script(topic)
        print(f"📖 Script Generated: {script['title']}")
        
        # Step 3: Voiceover
        audio_path = "temp/voiceover.mp3"
        os.makedirs("temp", exist_ok=True)
        self.audio_engine.generate(script['voiceover_text'], audio_path)
        
        # Step 4: B-Roll Generation (First prompt only for MVP)
        b_roll_path = "temp/broll_1.mp4"
        self.asset_engine.generate_video_clip(script['b_roll_prompts'][0], b_roll_path)
        
        # Step 5: Talking Avatar
        avatar_video_path = "temp/avatar_talking.mp4"
        self.asset_engine.generate_talking_avatar(self.avatar_ref, audio_path, avatar_video_path)
        
        # Step 6: Assemble
        final_video = self.assembler.assemble(
            [b_roll_path], 
            avatar_video_path, 
            audio_path, 
            script
        )
        
        # Step 7: Notify via Telegram
        self.notify(final_video, f"🎬 *Trendey Success!*\n\n*Topic:* {topic}\n*Title:* {script.get('title', 'Video Generated')}")
        
        print(f"🏆 MISSION COMPLETE: {final_video}")
        return final_video

    def notify(self, file_path, caption):
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        if not bot_token or not chat_id:
            print("⚠️ Telegram credentials missing. Skipping notification.")
            return

        print("📲 Sending video to Telegram...")
        url = f"https://api.telegram.org/bot{bot_token}/sendVideo"
        try:
            with open(file_path, "rb") as video:
                response = requests.post(url, data={
                    "chat_id": chat_id,
                    "caption": caption,
                    "parse_mode": "Markdown"
                }, files={"video": video})
                if response.status_code == 200:
                    print("✅ Telegram notification sent!")
                else:
                    print(f"❌ Telegram Error: {response.text}")
        except Exception as e:
            print(f"❌ Failed to send Telegram: {e}")

if __name__ == "__main__":
    agent = TrendeyOrchestrator()
    agent.run()
