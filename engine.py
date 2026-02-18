import os
import json
import requests
import asyncio
import edge_tts
from gradio_client import Client

class ScriptEngine:
    """Uses HF Inference API to generate topics and scripts."""
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("HF_TOKEN")
        self.api_url = "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-72B-Instruct"

    def query(self, prompt):
        if not self.api_key: return "Error: No HF_TOKEN"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"inputs": f"<|system|>\nYou are a viral YouTube content strategist.\n<|user|>\n{prompt}\n<|assistant|>", "parameters": {"max_new_tokens": 1500}}
        response = requests.post(self.api_url, headers=headers, json=payload)
        try:
            res = response.json()
            return res[0]['generated_text'].split("<|assistant|>")[-1].strip()
        except: return str(response.json())

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
        # Basic JSON extraction in case model adds markers
        if "```json" in response:
            response = response.split("```json")[-1].split("```")[0].strip()
        return json.loads(response)

class RemoteAssetEngine:
    """Triggering HF Spaces for Video and LipSync."""
    def __init__(self, video_space, lipsync_space):
        self.video_client = Client(video_space) if video_space else None
        self.lipsync_client = Client(lipsync_space) if lipsync_space else None

    def generate_video_clip(self, prompt, output_path):
        """Calls Wan-2.1 or LTX Space."""
        print(f"🎬 Generating B-Roll: {prompt}")
        result = self.video_client.predict(prompt=prompt, api_name="/generate")
        # result is usually a path to the file
        os.replace(result, output_path)
        return output_path

    def generate_talking_avatar(self, image_path, audio_path, output_path):
        """Calls LivePortrait / StableAvatar Space."""
        print(f"👤 Syncing Avatar {image_path} with Audio {audio_path}")
        result = self.lipsync_client.predict(image_path, audio_path, api_name="/predict")
        os.replace(result, output_path)
        return output_path

class AudioEngine:
    """Local TTS using Edge-TTS (No GPU needed)."""
    async def _gen(self, text, path):
        communicate = edge_tts.Communicate(text, "en-US-ChristopherNeural")
        await communicate.save(path)

    def generate(self, text, path):
        asyncio.run(self._gen(text, path))
        return path
