# 🎬 Trendey - The Viral Video Agent

**Trendey** is a high-performance, fully automated cinematic video generation pipeline. It leverages state-of-the-art AI models to transform trending topics into professional YouTube-ready videos with zero manual effort.

## ✨ Features
- **🤖 Automated Scripting**: Generates hooks, screenplays, and b-roll prompts using LLMs.
- **🎥 Cinematic Visuals**: Powered by **Wan-2.1 (14B)** for stunning 1080p video generation.
- **👤 Persistent Avatar**: Realistic AI-driven lip-syncing using **LivePortrait**.
- **🎙️ Studio-Quality Voice**: Crystal clear text-to-speech using **Edge-TTS**.
- **🚀 Cloud Orchestration**: Runs nightly via **GitHub Actions** using a "Guest Mode" GPU execution strategy—no local GPU required.

## 🛠️ Performance Architecture
Unlike traditional generators, Trendey uses an **Agentic Orchestrator** to coordinate specialized workers:
1. **Brain (Qwen-2.5)**: Strategic content planning.
2. **Video Engine (Wan-2.1)**: High-fidelity cinematic backgrounds.
3. **Avatar Engine (LivePortrait)**: Identity-preserving talking-head generation.
4. **Assembler (MoviePy)**: Final pixel-perfect stitching and audio mastering.

## 📦 Getting Started

### 1. Prerequisites
- [Hugging Face](https://huggingface.co/) Access Token (Free Tier).
- A GitHub account.

### 2. Local Setup
```bash
# Clone the repository
git clone https://github.com/yourusername/Trendey.git
cd Trendey

# Setup environment
cp .env.example .env
# Edit .env and add your HF_TOKEN
```

### 3. Usage (Local)
```bash
uv run --with-requirements requirements.txt python orchestrator.py
```

## 🤖 GitHub Automation
Trendey is built to be a "Nightly Factory":
1. Fork/Clone this repo.
2. Add your `HF_TOKEN` to **Settings > Secrets > Actions**.
3. The pipeline will automatically run every night at midnight UTC and generate a new video in your GitHub Artifacts.

## ⚖️ License
MIT License. Created by [A.K. Dey](https://github.com/a-k-dey).
