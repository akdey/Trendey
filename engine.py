import os
import json
import requests
import asyncio
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
            # Use the chat completion API which is the modern standard
            response = ""
            for message in self.client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                stream=True
            ):
                response += (message.choices[0].delta.content or "")
            return response.strip()
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
        """Calls Wan-2.1 Space with correct argument mapping."""
        print(f"🎬 Generating B-Roll: {prompt}")
        # Wan-2.1 T2V-14B Space: [prompt, neg_prompt, resolution, frames, steps, guidance, seed]
        # Signature: (prompt, negative_prompt, resolution, num_frames, num_inference_steps, guidance_scale, seed)
        result = self.video_client.predict(
            prompt,               # prompt
            "low quality, blurry", # negative_prompt
            "832x480",            # resolution
            81,                   # num_frames
            50,                   # num_inference_steps (Wan uses 50 for high quality)
            6.0,                  # guidance_scale
            -1,                   # seed
            api_name="/generate"
        )
        os.replace(result, output_path)
        return output_path

    def generate_talking_avatar(self, image_path, audio_path, output_path):
        """Calls LivePortrait / StableAvatar Space with correct mapping."""
        print(f"👤 Syncing Avatar {image_path} with Audio {audio_path}")
        # LivePortrait: [input_image, input_audio, flag_do_lip_sync]
        result = self.lipsync_client.predict(
            image_path, 
            audio_path, 
            True,        # flag_do_lip_sync
            api_name="/predict"
        )
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
