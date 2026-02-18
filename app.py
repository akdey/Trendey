import gradio as gr
import os
import torch
import time
from engine import VideoGenEngine

# --- Setup ---
OUTPUT_DIR = "generated_videos"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Initialize Engine (Lazy loading in generate function for HF Spaces)
engine = None

def get_engine(model_key):
    global engine
    if engine is None or engine.model_type != model_key:
        engine = VideoGenEngine(model_type=model_key)
        # Use 1.3B by default for T4 compatibility
        engine.load_model(model_key="wan-2.1-1.3b") 
    return engine

def generate_video(prompt, neg_prompt, model_choice, resolution, frames, steps, guidance, seed, add_audio):
    try:
        current_engine = get_engine(model_choice)
        
        # Parse resolution
        w, h = map(int, resolution.split("x"))
        
        # generation
        video_frames, used_seed, latency = current_engine.generate(
            prompt=prompt,
            negative_prompt=neg_prompt,
            width=w,
            height=h,
            num_frames=int(frames),
            steps=int(steps),
            guidance=float(guidance),
            seed=int(seed)
        )
        
        # Audio generation if requested
        audio_path = None
        if add_audio:
            audio_path = current_engine.generate_audio_bg(prompt)
            
        # Save
        filename = f"vid_{int(time.time())}.mp4"
        output_path = os.path.join(OUTPUT_DIR, filename)
        final_video_path = current_engine.save_result(video_frames, output_path, audio_path=audio_path)
        
        status = f"✅ Generated in {latency:.1f}s | Seed: {used_seed}"
        return final_video_path, status
        
    except Exception as e:
        return None, f"❌ Error: {str(e)}"

# --- Custom CSS for Premium Look ---
css = """
footer {visibility: hidden}
.gradio-container {background: #0b0f19; color: #e5e7eb;}
#title-container {text-align: center; margin-bottom: 2rem;}
#title-container h1 {
    background: linear-gradient(90deg, #6366f1, #a855f7, #ec4899);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 3rem;
    font-weight: 800;
}
.generate-btn {
    background: linear-gradient(90deg, #4f46e5, #9333ea) !important;
    border: none !important;
}
.generate-btn:hover {
    filter: brightness(1.2);
}
"""

# --- Gradio UI ---
with gr.Blocks(theme=gr.themes.Soft(), css=css) as demo:
    with gr.Div(elem_id="title-container"):
        gr.Markdown("# 🎬 Trendey Pro")
        gr.Markdown("### Next-Gen High Resolution AI Video for Content Creators")

    with gr.Row():
        with gr.Column(scale=1):
            with gr.Group():
                gr.Markdown("#### 📝 Prompt Configuration")
                prompt = gr.Textbox(
                    label="What do you want to see?",
                    placeholder="Realistic drone shot of a misty pine forest in the Italian Alps, morning sun rays, cinematic lighting, 8k, highly detailed...",
                    lines=3
                )
                neg_prompt = gr.Textbox(
                    label="Negative Prompt (What to exclude)",
                    value="blurry, low quality, watermark, text, distorted, ugly, grainy, choppy",
                    placeholder="e.g. low quality"
                )
            
            with gr.Accordion("⚙️ Engine Settings", open=True):
                model_choice = gr.Dropdown(
                    choices=["wan-2.1-1.3b", "wan-2.1-14b (ZeroGPU Required)", "ltx-video"],
                    value="wan-2.1-1.3b",
                    label="Engine Model"
                )
                resolution = gr.Radio(
                    choices=["832x480", "1280x720", "1920x1080", "480x832 (Portrait)"],
                    value="832x480",
                    label="Resolution"
                )
                frames = gr.Slider(minimum=16, maximum=129, value=81, step=16, label="Number of Frames")
                add_audio = gr.Checkbox(label="🔊 Generate Dynamic Background Music (AI)", value=False)
                
            with gr.Accordion("🧪 Advanced Parameters", open=False):
                steps = gr.Slider(minimum=20, maximum=100, value=50, step=1, label="Inference Steps")
                guidance = gr.Slider(minimum=1.0, maximum=15.0, value=6.0, step=0.5, label="Guidance Scale")
                seed = gr.Number(value=-1, label="Seed (-1 for Random)", precision=0)
            
            generate_btn = gr.Button("🚀 Generate Masterpiece", variant="primary", elem_classes="generate-btn")

        with gr.Column(scale=1.2):
            with gr.Group():
                gr.Markdown("#### 📺 Preview Output")
                video_output = gr.Video(label="Generated Video", interactive=False)
                status_box = gr.Textbox(label="Status & Meta", interactive=False)
            
            with gr.Group():
                gr.Markdown("#### 💡 Pro Tips for YT")
                gr.Markdown("""
                - **Cinematic Shots**: Use keywords like 'drone shot', 'depth of field', 'golden hour'.
                - **Motion Control**: Add 'slow motion', 'fast camera movement', or 'static shot' to guide the AI.
                - **Resolution**: 1280x720 is ideal for YouTube, but 832x480 is faster for testing.
                - **Audio**: Sync with trending audio in your editor for best reach!
                """)

    generate_btn.click(
        fn=generate_video,
        inputs=[prompt, neg_prompt, model_choice, resolution, frames, steps, guidance, seed, add_audio],
        outputs=[video_output, status_box]
    )

    gr.Examples(
        examples=[
            ["A futuristic cyberpunk city with neon lights reflecting on wet streets, flying cars in the distance, cinematic lighting", "low quality, blurry", "wan-2.1-1.3b", "832x480", 81, 50, 6.0, -1, True],
            ["Macro shot of a butterfly opening its wings in a lush garden, morning dew on leaves, 4k", "low quality, blurry", "wan-2.1-1.3b", "832x480", 81, 50, 6.0, -1, False],
        ],
        inputs=[prompt, neg_prompt, model_choice, resolution, frames, steps, guidance, seed, add_audio],
        outputs=[video_output, status_box]
    )

if __name__ == "__main__":
    demo.queue().launch(share=False)
