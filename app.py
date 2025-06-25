import os
import base64
import json
import re
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import boto3
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

# Configuration settings for the chatbot
CHATBOT_CONFIG = {
    "json_data_path": "c:/Users/LinoG/source/repos/pronunciation-agent/felinos.json",  # Use direct file path
    "user_name": "Lino"  # Add user name configuration
}

app = Flask(__name__)
CORS(app)

# Conversation memory for a single user (demo).
# In production, store per-user sessions in a DB or similar.
conversation_history = [
    {
        "role": "system",
        "content": (
            "Tu nombre es ChatManitas. Eres un asistente amigable que responde siempre en español. "
            f"El usuario se llama {CHATBOT_CONFIG['user_name']}. Dirígete a él por su nombre cuando sea oportuno, "
            "por ejemplo en saludos o cuando quieras hacer la conversación más personal. "
            "Debes mantener una conversación natural y responder de manera atenta y servicial. "
            "Cuando el usuario te pida cargar o consultar datos JSON, el sistema (no tú) cargará "
            "automáticamente los datos del archivo felinos.json que está configurado en el servidor. "
            "No has recibido ningún archivo directamente del usuario. "
            "Cuando los datos sean cargados, se te proporcionarán en el contexto de la conversación. "
            "Utiliza ÚNICAMENTE la información proporcionada para responder a las preguntas, sin inventar datos adicionales."
        )
    }
]

# Variable to store JSON context for the conversation
json_context = {}

def load_json_from_file(file_path):
    """Load JSON data from a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return {"error": f"Error: The file {file_path} was not found"}
    except json.JSONDecodeError:
        return {"error": "The file did not contain valid JSON data"}
    except Exception as e:
        return {"error": f"Error loading JSON file: {str(e)}"}

@app.route('/chat', methods=['POST'])
def chat():
    """
    Endpoint to handle either:
      - Audio input (multipart/form-data, 'file')
      - Text input (JSON, 'message')
      
    Then we pass user input to GPT (with conversation history),
    get a response, synthesize TTS, and return both text + audio.
    """
    global json_context
    global conversation_history
    user_message = None

    # Check if an audio file was uploaded
    if 'file' in request.files:
        audio_file = request.files['file']
        audio_path = 'user_audio.mp3'
        audio_file.save(audio_path)

        # Transcribe user audio
        user_message = transcribe_with_whisper(audio_path)
        print(f"Transcribed message: {user_message}")  # Debug logging
    else:
        data = request.get_json()
        user_message = data.get('message', '')

    if not user_message:
        return jsonify({"error": "No user message provided"}), 400

    # Check if the user is asking to load the JSON data (simple keyword detection)
    load_keywords = ["carga los datos", "carga el json", "carga la información", "usa los datos"]
    
    if any(keyword in user_message.lower() for keyword in load_keywords):
        # Reset conversation history to start fresh with new data
        conversation_history = [
            {
                "role": "system",
                "content": (
                    "Tu nombre es ChatManitas. Eres un asistente amigable que responde siempre en español. "
                    f"El usuario se llama {CHATBOT_CONFIG['user_name']}. Dirígete a él por su nombre cuando sea oportuno. "
                    "Debes mantener una conversación natural y responder de manera atenta y servicial. "
                    "A continuación, te proporcionaré datos sobre gatos. Utiliza SOLO estos datos para responder preguntas. "
                    "NO inventes ningún dato que no esté explícitamente en esta información. "
                    "IMPORTANTE: NO debes usar formato Markdown en tus respuestas, ya que el cliente no lo soporta. "
                    "Usa formato de texto plano para listas, tablas, etc."
                )
            }
        ]
        
        # Load JSON from the configured file path
        json_context = load_json_from_file(CHATBOT_CONFIG['json_data_path'])
        
        if 'error' in json_context:
            error_message = json_context['error']
            context_message = {
                "role": "system", 
                "content": f"Hubo un error al cargar los datos JSON: {error_message}"
            }
            conversation_history.append(context_message)
        else:
            # Create a simple list of cat names first
            cat_names = [cat.get('nombre', 'Sin nombre') for cat in json_context]
            cats_names_list = "Los gatos disponibles son: " + ", ".join(cat_names)
            
            # Create explicit facts about the cats with precise calculations
            cat_facts = []
            max_tuna_cat = {"name": "", "total": 0}
            max_sick_cat = {"name": "", "total": 0}
            
            for cat in json_context:
                name = cat.get('nombre', 'Sin nombre')
                cat_facts.append(f"Gato: {name}")
                cat_facts.append(f"- Raza: {cat.get('raza', 'desconocida')}")
                cat_facts.append(f"- Edad: {cat.get('edad', 'edad desconocida')}")
                cat_facts.append(f"- Sexo: {cat.get('sexo', 'sexo desconocido')}")
                
                if 'esterilizado' in cat:
                    cat_facts.append(f"- Esterilizado: {'Sí' if cat['esterilizado'] else 'No'}")
                
                if 'historia_ultimos_6_meses' in cat:
                    hist = cat['historia_ultimos_6_meses']
                    if 'veces_enfermo' in hist:
                        times_sick = hist['veces_enfermo']
                        cat_facts.append(f"- Veces enfermo: {times_sick}")
                        
                        # Check if this cat has been sick more times than current max
                        if times_sick > max_sick_cat["total"]:
                            max_sick_cat["name"] = name
                            max_sick_cat["total"] = times_sick
                    
                    if 'porciones_atun_oz_mensual' in hist:
                        portions = hist['porciones_atun_oz_mensual']
                        total = sum(portions)
                        cat_facts.append(f"- Total onzas atún: {total}")
                        
                        # Check if this cat has consumed more tuna than current max
                        if total > max_tuna_cat["total"]:
                            max_tuna_cat["name"] = name
                            max_tuna_cat["total"] = total
                
                cat_facts.append("") # Empty line between cats
            
            # Join all facts with line breaks
            all_facts = "\n".join(cat_facts)
            
            # Add summary information about key statistics
            summary_facts = [
                f"El gato que ha consumido más atún es {max_tuna_cat['name']} con un total de {max_tuna_cat['total']} onzas.",
                f"El gato que ha estado enfermo más veces es {max_sick_cat['name']} con un total de {max_sick_cat['total']} veces."
            ]
            
            # Add the list of cat names, facts, and summary to the conversation context
            context_message = {
                "role": "system", 
                "content": (
                    f"El sistema ha cargado datos de {len(json_context)} gatos.\n\n"
                    f"{cats_names_list}\n\n"
                    f"Datos completos:\n{all_facts}\n\n"
                    f"Resumen estadístico:\n"
                    f"- {summary_facts[0]}\n"
                    f"- {summary_facts[1]}\n\n"
                    "IMPORTANTE: Responde ÚNICAMENTE con esta información. NO inventes gatos, nombres, o datos que no aparezcan "
                    "explícitamente en este listado. NO uses formato Markdown. Usa texto plano."
                )
            }
            conversation_history.append(context_message)
            
            # Add a confirmation message to the conversation
            confirmation_message = f"He cargado la información de los gatos, {CHATBOT_CONFIG['user_name']}. Estoy listo para responder tus preguntas sobre ellos."
            conversation_history.append({
                "role": "assistant", 
                "content": confirmation_message
            })
            
            # Return early with just the confirmation message
            audio_base64 = synthesize_with_polly(confirmation_message)
            return jsonify({
                "bot_text": confirmation_message,
                "bot_audio": audio_base64.decode('utf-8'),
                "conversation_history": conversation_history
            })

    # Append user's message to conversation history
    conversation_history.append({"role": "user", "content": user_message})

    # Add special instruction for list or table questions
    if any(keyword in user_message.lower() for keyword in ["lista", "tabla", "mostrar", "dame", "cuáles", "nombres"]):
        instruction = {
            "role": "system",
            "content": (
                "El usuario está solicitando información en formato de lista o tabla. "
                "Considera lo siguiente:\n"
                "1. Utiliza ÚNICAMENTE los datos proporcionados en el contexto\n"
                "2. NO uses formato Markdown, usa texto plano\n"
                "3. Si muestras una lista de datos numerada, añade un mensaje corto al final\n"
                "4. Separa la información tabular del mensaje final con una línea en blanco\n"
                "5. NO inventes información\n"
                "6. Responde de forma directa y concisa\n"
                "7. IMPORTANTE: Tu respuesta debe tener dos partes: los datos solicitados y un mensaje final. "
                "El mensaje final debe ser breve y amigable para que se pueda leer por audio."
            )
        }
        conversation_history.append(instruction)

    # GPT call with entire conversation history but at lower temperature
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=conversation_history,
        temperature=0.1,  # Even lower temperature for factual responses
        max_tokens=1000
    )

    bot_message = response.choices[0].message.content.strip()
    conversation_history.append({"role": "assistant", "content": bot_message})

    # Process the bot message for audio
    audio_base64 = None
    
    # If the message contains data presentation (list/table) + closing message
    if any(keyword in user_message.lower() for keyword in ["lista", "tabla", "mostrar", "dame", "cuáles", "nombres"]):
        # Try to split the message between data and closing remark
        message_parts = re.split(r'\n\s*\n', bot_message)
        
        if len(message_parts) > 1:
            # The last paragraph is likely the closing remark
            data_part = "\n\n".join(message_parts[:-1])
            closing_remark = message_parts[-1]
            
            # Only synthesize the closing remark
            audio_base64 = synthesize_with_polly(closing_remark)
            audio_base64 = audio_base64.decode('utf-8')
            
            response_data = {
                "bot_text": bot_message,
                "bot_audio": audio_base64,
                "audio_text": closing_remark,  # Include what text was actually spoken
                "conversation_history": conversation_history
            }
        else:
            # If we can't identify a clear closing remark, synthesize nothing
            response_data = {
                "bot_text": bot_message,
                "no_audio": True,
                "audio_message": "La respuesta contiene solo información tabular que se muestra visualmente.",
                "conversation_history": conversation_history
            }
    else:
        # Regular response, synthesize the whole thing
        audio_base64 = synthesize_with_polly(bot_message)
        audio_base64 = audio_base64.decode('utf-8')
        
        response_data = {
            "bot_text": bot_message,
            "bot_audio": audio_base64,
            "conversation_history": conversation_history
        }

    return jsonify(response_data)

def transcribe_with_whisper(audio_filepath):
    with open(audio_filepath, "rb") as audio:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            language="es",
            file=audio
        )
    return transcription.text

def synthesize_with_polly(text):
    response = polly_client.synthesize_speech(
        Text=text,
        OutputFormat='mp3',
        VoiceId='Lupe',  # Spanish voice
        Engine='neural',
        LanguageCode='es-US'  # Spanish language code
    )
    audio_bytes = response['AudioStream'].read()
    return base64.b64encode(audio_bytes)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
