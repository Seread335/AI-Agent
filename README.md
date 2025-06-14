# AI Agent System

A sophisticated AI Agent system that intelligently routes tasks between multiple specialized AI models to provide comprehensive assistance across various domains.

[![GitHub license](https://img.shields.io/github/license/Seread335/AI-Agent)](https://github.com/Seread335/AI-Agent/blob/main/LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green)](https://fastapi.tiangolo.com/)

## Features

- 🤖 Multi-model integration and orchestration
- 🧠 Intelligent task routing system
- 🔄 Advanced response synthesis
- ⚡ Real-time streaming support
- 📊 Comprehensive performance monitoring
- 💬 Conversation context management
- 🛡️ Robust error handling and fallback mechanisms

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ai-agent.git
cd ai-agent
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate   # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables (create a .env file):
```env
DEEPSEEK_API_KEY=your_api_key
QWEN_API_KEY=your_api_key
AGENTICA_API_KEY=your_api_key
```

5. Run the application:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Visit `http://localhost:8000/docs` for API documentation.

## Models Integrated

- DeepSeek R1 0528: Specialized in reasoning, analysis, and complex problem-solving
- Qwen3 8B: Handles general conversation, creative writing, and summarization
- Agentica Deepcoder 14B: Focused on coding, debugging, and technical documentation
- Qwen2.5 Coder 32B: Advanced coding, system architecture, and algorithm design

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure the system by editing `config.yaml`

3. Set up environment variables for API keys:
```bash
export DEEPSEEK_API_KEY="your-api-key"
export QWEN_API_KEY="your-api-key"
export AGENTICA_API_KEY="your-api-key"
```

4. Run the server:
```bash
python main.py
```

## API Usage

### REST API

Make a POST request to `/query`:
```json
{
    "query": "Your question or task here",
    "context": {},  // Optional
    "user_id": "user123"  // Optional
}
```

### WebSocket API

Connect to `/ws` for real-time streaming responses.

## Project Structure

```
├── core/
│   ├── agent.py              # Main agent orchestrator
│   ├── model_manager.py      # Model integration and management
│   ├── task_router.py        # Intelligent task routing
│   └── response_synthesizer.py # Multi-model response handling
├── utils/
│   ├── logger.py            # Logging configuration
│   ├── config.py            # Configuration management
│   ├── context_manager.py   # Conversation context handling
│   └── performance_monitor.py # Performance tracking
├── main.py                  # FastAPI application
├── config.yaml              # System configuration
└── requirements.txt         # Project dependencies
```

## Performance Monitoring

The system includes comprehensive performance monitoring:
- Response times
- Model usage statistics
- Task success rates
- Error tracking
- Resource utilization

Performance metrics are stored in `logs/metrics.json`.

## Error Handling

The system implements multiple layers of error handling:
- Individual model failures
- Task routing fallbacks
- Response synthesis recovery
- API error handling
- Connection management

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

MIT License
=======
# AI-Agent
>>>>>>> origin/main
