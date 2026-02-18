import os
import json
import requests
import asyncio
import time
import edge_tts
from gradio_client import Client

from huggingface_hub import InferenceClient

class ScriptEngine:
    """Uses HF Inference API to generate topics and scripts."""
    def __init__(self, api_key=None):
        self.api_key = api_key or (os.getenv("HF_TOKEN") or "").strip()
        # Use InferenceClient which handles the router/endpoint logic automatically
        self.client = InferenceClient("Qwen/Qwen2.5-72B-Instruct", token=self.api_key)

    def query(self, prompt):
        if not self.api_key: return "Error: No HF_TOKEN"
        try:
            # Simplified non-streaming call for better stability
            response = self.client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error from HF API: {str(e)}"

    def get_viral_topic(self):
        prompt = "Search trends for 2026. Give me ONE high-CPM, viral topic for a 60-second video. Just the topic name."
        return self.query(prompt)

    def generate_full_script(self, topic):
        prompt = f"""Create a 60s YouTube script for '{topic}'. 
        Return ONLY valid JSON with this structure:
        {{
            "title": "...",
            "voiceover_text": "...",
            "b_roll_prompts": ["prompt 1", "prompt 2", "prompt 3"],
            "avatar_schedule": [
                {{"time": 0, "position": "center", "action": "intro"}},
                {{"time": 10, "position": "corner", "action": "talk"}},
                {{"time": 50, "position": "center", "action": "outro"}}
            ]
        }}
        """
        response = self.query(prompt)
        print(f"DEBUG: LLM Response length: {len(response)}")
        
        # Robust extraction
        try:
            if "```json" in response:
                response = response.split("```json")[-1].split("```")[0].strip()
            # If the model didn't use blocks, try to find the first '{' and last '}'
            elif "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                response = response[start:end]
            
            return json.loads(response)
        except Exception as e:
            print(f"❌ JSON Parse Error: {e}\nResponse was: {response[:200]}...")
            # Return a fallback script to prevent crash
            return {
                "title": f"The Future of {topic}",
                "voiceover_text": f"Welcome! Today we talk about {topic}.",
                "b_roll_prompts": [f"{topic} cinematic visual"],
                "avatar_schedule": [{"time": 0, "position": "center", "action": "intro"}]
            }

class RemoteAssetEngine:
    """Triggering HF Spaces for Video and LipSync."""
    def __init__(self, video_space, lipsync_space, hf_token=None):
        self.hf_token = hf_token
        self.video_client = Client(video_space, token=self.hf_token) if video_space else None
        self.lipsync_client = Client(lipsync_space, token=self.hf_token) if lipsync_space else None
    def generate_video_clip(self, prompt, output_path):
        """Asynchronous generation with status polling for Wan-2.1."""
        print(f"🎬 Initializing Async Video Generation: {prompt}")
        try:
            # Step 1: Trigger the generation
            # API: /t2v_generation_async (prompt, size, watermark, seed)
            print("   🚀 Triggering /t2v_generation_async...")
            trigger_result = self.video_client.predict(
                prompt,         # prompt
                "1280*720",     # size
                True,           # watermark_wan
                -1.0,           # seed
                api_name="/t2v_generation_async"
            )
            print(f"   🕒 Job started. Estimated wait: {trigger_result[1]}s")
            
            # Step 2: Poll for status
            max_retries = 40 # Up to 10 minutes
            for i in range(max_retries):
                time.sleep(15) 
                print(f"   🔄 Polling status (Attempt {i+1})...")
                
                status = self.video_client.predict(api_name="/status_refresh")
                video_info = status[0]
                if video_info and isinstance(video_info, dict) and video_info.get("video"):
                    video_file = video_info["video"]
                    print(f"   ✅ Video generation complete: {video_file}")
                    os.replace(video_file, output_path)
                    return output_path
                
                progress = status[3] if len(status) > 3 else "Unknown"
                print(f"   ⏳ Progress: {progress}%")
                
            raise Exception("Video generation timed out.")
            
        except Exception as e:
            print(f"❌ Video Generation Failed: {str(e)}")
            raise e

    def generate_talking_avatar(self, image_path, audio_path, output_path):
        """Calls LivePortrait with fallback and robust return handling."""
        print(f"👤 Syncing Avatar {image_path} with Audio {audio_path}")
        # Args: [input_image, input_audio, flag_do_lip_sync]
        args = [image_path, audio_path, True]
        
        for name in ["/predict", "/process"]:
            try:
                result = self.lipsync_client.predict(*args, api_name=name)
                file_path = result
                if isinstance(result, dict): file_path = result.get("video") or result.get("path")
                elif isinstance(result, (list, tuple)): file_path = result[0]
                os.replace(file_path, output_path)
                return output_path
            except Exception:
                continue
        
        try:
            print("   ⚠️ Avatar API names failed. Falling back to fn_index=0...")
            result = self.lipsync_client.predict(*args, fn_index=0)
            file_path = result
            if isinstance(result, dict): file_path = result.get("video") or result.get("path")
            elif isinstance(result, (list, tuple)): file_path = result[0]
            os.replace(file_path, output_path)
            return output_path
        except Exception as e:
            print(f"❌ Avatar Generation Failed: {str(e)}")
            raise e

class AudioEngine:
    """Local TTS using Edge-TTS (No GPU needed)."""
    async def _gen(self, text, path):
        communicate = edge_tts.Communicate(text, "en-US-ChristopherNeural")
        await communicate.save(path)

    def generate(self, text, path):
        asyncio.run(self._gen(text, path))
        return path
