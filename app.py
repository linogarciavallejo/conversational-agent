import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from openai import OpenAI
import requests
import base64
import boto3
from flask_cors import CORS 

# Load environment variables first
load_dotenv()

# Initialize OpenAI client
api_key = os.getenv('OPENAI_API_KEY')  # Use getenv() instead of environ.get for consistency
client = OpenAI(api_key=api_key)  # Fixed: added keyword argument

# Initialize AWS Polly client
polly_client = boto3.client(
    'polly',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_DEFAULT_REGION')
)

app = Flask(__name__)
CORS(app)

@app.route('/evaluate-pronunciation', methods=['POST'])
def evaluate_pronunciation():
    audio_file = request.files['file']
    audio_path = 'user_audio.mp3'
    audio_file.save(audio_path)

    transcript = transcribe_with_whisper(audio_path)
    evaluation = evaluate_with_gpt(transcript)
    feedback_audio = synthesize_with_polly(evaluation)

    return jsonify({
        'transcript': transcript,
        'evaluation': evaluation,
        'feedback_audio': feedback_audio.decode('utf-8')
    })

def transcribe_with_whisper(audio_filepath):
    with open(audio_filepath, "rb") as audio:
        transcription = client.audio.transcriptions.create(
            model="whisper-1", 
            language="en",
            file=audio
        )
    return transcription.text

def evaluate_with_gpt(transcript):
    system_message = """
    You are a friendly English pronunciation coach, specialized in teaching North American English. 
    When the user gives you text from a speech recognition system, 
    you will assume it reflects their actual speech. 
    Your job is to provide:
    1) Specific phonetic feedback on any likely mispronunciations
    2) A severity rating (1=very minor, 5=severe)
    3) Encouraging suggestions for improvement

    Do not mention that you cannot hear them or that you lack audio.
    Focus purely on the recognized text.
    """

    user_message = f"""
    Here is the recognized transcript of what the user said:
    "{transcript}"
    Please provide your feedback accordingly.
    """

    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ],
        temperature=0.3
    )
    
    return response.choices[0].message.content.strip()

def synthesize_with_polly(text):
    response = polly_client.synthesize_speech(
        Text=text,
        OutputFormat='mp3',
        VoiceId='Joanna',
        Engine='neural'
    )
    
    # Correct way to handle the audio stream
    if 'AudioStream' in response:
        with response['AudioStream'] as stream:
            audio_bytes = stream.read()
        return base64.b64encode(audio_bytes)
    else:
        raise ValueError("No audio stream found in Polly response")

if __name__ == '__main__':
    app.run(debug=True, port=5000)