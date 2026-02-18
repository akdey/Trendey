import os
import requests
from dotenv import load_dotenv

load_dotenv()

class TelegramInterface:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.github_token = os.getenv("GH_PAT")  # GitHub Personal Access Token
        self.repo = os.getenv("GH_REPO")         # e.g. "username/Trendey"

    def send_message(self, text, reply_markup=None):
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        return requests.post(url, json=payload).json()

    def send_topic_options(self, topics):
        keyboard = {
            "keyboard": [[{"text": t}] for t in topics],
            "one_time_keyboard": True,
            "resize_keyboard": True
        }
        self.send_message("📌 *Trendey Intelligence* has found some viral topics. Which one should I produce?", keyboard)

    def trigger_github_workflow(self, topic):
        """Triggers the GitHub Action remotely."""
        url = f"https://api.huggingface.co/repos/{self.repo}/actions/workflows/pipeline.yml/dispatches"
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        payload = {
            "ref": "main",
            "inputs": {"topic": topic}
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 204:
            self.send_message(f"🚀 *Mission Acknowledged!*\n\nGenerating video for: `{topic}`\nI will send the result here once complete.")
        else:
            self.send_message(f"❌ *Failed to trigger GitHub:* {response.text}")

if __name__ == "__main__":
    # This part would normally be in a polling loop or webhook
    pass
