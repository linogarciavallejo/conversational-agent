import os
import base64
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import boto3
import requests
from flask_cors import CORS
from openai import OpenAI

load_dotenv()

api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)

polly_client = boto3.client(
    'polly',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_DEFAULT_REGION')
)

app = Flask(__name__)
CORS(app)

# Conversation memory for a single user (demo).
# In production, store per-user sessions in a DB or similar.
conversation_history = [
    {
        "role": "system",
        "content": (
            "You are a friendly English tutor and conversation partner, specialized "
            "in teaching North American English pronunciation. You will: "
            "1) Have a normal conversation with the user, "
            "2) Provide specific pronunciation corrections whenever relevant, "
            "3) Respond in a supportive, engaging manner. "
            "Use the context of the conversation to maintain continuity."
        )
    }
]

@app.route('/chat', methods=['POST'])
def chat():
    """
    Endpoint to handle either:
      - Audio input (multipart/form-data, 'file')
      - Text input (JSON, 'message')
    Then we pass user input to GPT (with conversation history),
    get a response, synthesize TTS, and return both text + audio.
    """
    user_message = None

    # Check if an audio file was uploaded
    if 'file' in request.files:
        audio_file = request.files['file']
        audio_path = 'user_audio.mp3'
        audio_file.save(audio_path)

        # Transcribe user audio (forced English)
        user_message = transcribe_with_whisper(audio_path)
    else:
        data = request.get_json()
        user_message = data.get('message', '')

    if not user_message:
        return jsonify({"error": "No user message provided"}), 400

    # Append user's message to conversation history
    conversation_history.append({"role": "user", "content": user_message})

    # GPT call with entire conversation history
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=conversation_history,
        temperature=0.7
    )

    bot_message = response.choices[0].message.content.strip()
    conversation_history.append({"role": "assistant", "content": bot_message})

    # Synthesize TTS using AWS Polly
    audio_base64 = synthesize_with_polly(bot_message)

    return jsonify({
        "bot_text": bot_message,
        "bot_audio": audio_base64.decode('utf-8'),
        "conversation_history": conversation_history
    })

def transcribe_with_whisper(audio_filepath):
    with open(audio_filepath, "rb") as audio:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            language="en",
            file=audio
        )
    return transcription.text

def synthesize_with_polly(text):
    response = polly_client.synthesize_speech(
        Text=text,
        OutputFormat='mp3',
        VoiceId='Joanna',
        Engine='neural'
    )
    audio_bytes = response['AudioStream'].read()
    return base64.b64encode(audio_bytes)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
