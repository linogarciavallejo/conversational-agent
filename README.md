# ChatManitas - Pronunciation Agent

A conversational AI agent that combines speech recognition, natural language processing, and text-to-speech capabilities to provide an interactive voice assistant experience in Spanish.

## 🚀 Features

- **Voice Input**: Speech-to-text transcription using OpenAI Whisper
- **Text Input**: Direct text message support
- **Natural Language Processing**: GPT-4 Turbo for intelligent conversation
- **Text-to-Speech**: AWS Polly neural voice synthesis in Spanish
- **JSON Data Integration**: Dynamic loading and querying of structured data
- **Conversation Memory**: Maintains conversation context across interactions
- **CORS Support**: Cross-origin resource sharing for web applications

## 🏗️ Architecture

The application is built using Flask and integrates multiple AI services:

- **Backend**: Flask web server with RESTful API
- **Speech Recognition**: OpenAI Whisper API
- **Language Model**: OpenAI GPT-4 Turbo
- **Text-to-Speech**: AWS Polly with Spanish neural voice (Lupe)
- **Data Storage**: JSON file-based data management

## 📋 Prerequisites

- Python 3.8+
- OpenAI API key
- AWS credentials (for Polly TTS)
- Virtual environment (recommended)

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd pronunciation-agent
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv pagentenv
   # On Windows:
   .\pagentenv\Scripts\activate
   # On macOS/Linux:
   source pagentenv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   Create a `.env` file in the project root:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   AWS_ACCESS_KEY_ID=your_aws_access_key_id
   AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
   AWS_DEFAULT_REGION=us-east-1
   ```

## 🚀 Usage

1. **Start the server**:
   ```bash
   python app.py
   ```
   The server will start on `http://localhost:5000`

2. **API Endpoints**:

   ### POST /chat
   Handles both voice and text interactions.

   **Text Input**:
   ```json
   {
     "message": "Hola, ¿cómo estás?"
   }
   ```

   **Audio Input**:
   Send as multipart/form-data with audio file in 'file' field.

   **Response**:
   ```json
   {
     "bot_text": "Respuesta del asistente",
     "bot_audio": "base64_encoded_audio",
     "conversation_history": [...],
     "audio_text": "Texto que fue sintetizado a audio"
   }
   ```

## 📊 Data Integration

The system can load and query JSON data dynamically. Use phrases like:
- "Carga los datos"
- "Carga el JSON"
- "Usa los datos"

The application currently supports cat data (`felinos.json`) with the following structure:
```json
[
  {
    "nombre": "Luna",
    "raza": "Mestizo",
    "edad": "2 años",
    "sexo": "Hembra",
    "esterilizado": true,
    "historia_ultimos_6_meses": {
      "veces_enfermo": 1,
      "porciones_atun_oz_mensual": [5, 6, 4, 7, 5, 6]
    }
  }
]
```

## 🎯 Key Features

### Intelligent Response Processing
- **Data Queries**: Automatically calculates statistics and summaries
- **List/Table Requests**: Optimized audio synthesis for structured data
- **Context Awareness**: Maintains conversation flow and user preferences

### Audio Processing
- **Input**: Supports various audio formats for speech input
- **Output**: High-quality Spanish neural voice synthesis
- **Optimization**: Smart audio generation for different response types

### Conversation Management
- **Memory**: Persistent conversation history during session
- **Context**: Maintains user preferences and loaded data context
- **Personalization**: Addresses user by name (configurable)

## ⚙️ Configuration

The application can be configured through the `CHATBOT_CONFIG` dictionary in `app.py`:

```python
CHATBOT_CONFIG = {
    "json_data_path": "path/to/your/data.json",
    "user_name": "YourName"
}
```

## 🔧 Development

### Project Structure
```
pronunciation-agent/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── felinos.json          # Sample data file
├── user_audio.mp3        # Temporary audio storage
├── pagentenv/            # Virtual environment
└── README.md             # This file
```

### Adding New Data Sources
1. Create your JSON data file
2. Update `json_data_path` in `CHATBOT_CONFIG`
3. Modify the data processing logic in the `/chat` endpoint if needed

## 🚨 Error Handling

The application includes comprehensive error handling for:
- File not found errors
- Invalid JSON data
- API communication failures
- Audio processing issues

## 📝 API Response Types

### Standard Response
```json
{
  "bot_text": "Full response text",
  "bot_audio": "base64_encoded_audio",
  "conversation_history": [...]
}
```

### Data Loading Response
```json
{
  "bot_text": "Confirmation message",
  "bot_audio": "base64_encoded_audio",
  "conversation_history": [...]
}
```

### List/Table Response
```json
{
  "bot_text": "Full response with data",
  "bot_audio": "base64_encoded_closing_remark",
  "audio_text": "Text that was spoken",
  "conversation_history": [...]
}
```

## 🔒 Security Notes

- Store API keys securely in environment variables
- Use HTTPS in production
- Implement rate limiting for production use
- Validate file uploads and input data

## 📄 License

This project is licensed under the terms specified in the LICENSE file.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For questions or issues, please refer to the project documentation or create an issue in the repository.
