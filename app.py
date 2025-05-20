import os
import re
from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr
from googleapiclient.discovery import build #for YT

# Load API keys
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
yt_api_key = os.getenv('YOUTUBE_API')

def get_video_comments(video_link):

     # Regular expression to extract video ID from YouTube URL
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", video_link)
    
    if not match:
        yield "❌ Invalid YouTube video link. Please enter a valid YouTube video URL."
        return
    
    video_id = match.group(1)
    youtube = build("youtube", "v3", developerKey=yt_api_key)
    request = youtube.commentThreads().list(part="snippet", videoId=video_id, maxResults=20)
    response = request.execute()
    
    #comments = [item["snippet"]["topLevelComment"]["snippet"]["textDisplay"] for item in response.get("items", [])]
    #return "\n".join(comments)

    comments_list = []

    for item in response["items"]:
        comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
        comments_list.append(comment)

    system_message = "You are an assistant that analyse youtube comments"
    user_prompt = f"analyse the following comments by telling the channel owner about 1)overall 2)strengths of the video 3)weaknesses of the video 4)what is the future demands from the viewers. The \
    the comments are: {comments_list}"

    prompts = [
    {"role": "system", "content": system_message},
    {"role": "user", "content": user_prompt}]

    openai = OpenAI()
    MODEL_GPT = 'gpt-4o-mini'
    stream = openai.chat.completions.create(model=MODEL_GPT, messages=prompts,stream=True)
    
    response = ""

    for chunk in stream:
        if chunk.choices[0].delta.content:
            response += chunk.choices[0].delta.content or ""
            yield response

#Gradio UI
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🎥 YouTube Comment Analyzer")

    with gr.Row():
        with gr.Column(scale=1):
            video_input = gr.Textbox(label="📺 Enter YouTube Video Link")
            analyze_button = gr.Button("🔍 Analyze")

        with gr.Column(scale=2):
            analysis_output = [gr.Markdown()]

    analyze_button.click(
        fn=get_video_comments,
        inputs=video_input,
        outputs=analysis_output
    )

demo.launch(share=True)
