# Anthropic-OpenAI Agent

A powerful conversational agent system combining Anthropic's Claude and OpenAI APIs with web search capabilities.

## Features

- Cross-API integration between Anthropic and OpenAI
- Web search capabilities:
  - Simple Web Search: Parallel searches with intelligent aggregation
  - Deep Iterative Web Search: Multi-level research with successive refinements
- Automatic search strategy selection based on query complexity
- Streaming support for real-time AI responses
- Extensible tool framework
- Multiple interfaces:
  - Command-line interface
  - Web API (FastAPI)
  - Web UI (Next.js)

## Installation

### Prerequisites

- Python 3.12+
- Node.js 18+ (for the frontend)
- API keys for Anthropic and OpenAI

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/anthropic-openai.git
cd anthropic-openai
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

3. Create a `.env` file in the root directory with your API keys and other configuration:
```
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENAI_API_KEY=your_openai_api_key
SECRET_KEY=your_secret_key_for_jwt_tokens
DATABASE_URL=sqlite:///./data/anthropic_chatbot.db  # Default SQLite database path
```

4. Install frontend dependencies:
```bash
cd frontend
npm install
```

## Usage

### CLI Mode

```bash
python -m src launch-engine
```

### API Server

```bash
python -m src launch-server --reload
```

The API will be available at http://localhost:8000 with the following endpoints:
- `/chat` - For general chat interactions
- `/chat/ws/{token}` - WebSocket endpoint for streaming chat
- `/search` - For search capabilities
- `/users` - User management (registration, profile)
- `/token` - Authentication token endpoint
- `/conversations` - Conversation management
- `/projects` - Project/folder management

### Web UI

```bash
cd frontend
npm run dev
```

The web interface will be available at http://localhost:3000

## Architecture

### Backend Components

- `agent_loop.py`: Core conversation agent implementation
- `definitions.py`: Tool definitions and system prompts
- `types.py`: Type definitions for the system
- `api/`: FastAPI implementation
  - `app.py`: Main FastAPI application
  - `routers/`: API route handlers
  - `models/`: Pydantic models for request/response validation

### Frontend Components

- Next.js application with the following features:
  - ChatGPT-like interface with conversation history
  - Project/folder organization for conversations
  - Ability to pin important conversations
  - User authentication system
  - Streaming support for real-time AI responses
  - Search interface with configuration options
  - Responsive design with Tailwind CSS

## Extending the System

### Adding New Tools

1. Define your tool schema in `definitions.py`:
```python
my_new_tool = {
    "name": "my_new_tool",
    "description": "Description of what the tool does",
    "input_schema": {
        "type": "object",
        "properties": {
            "param1": {"type": "string", "description": "Description of parameter 1"},
            "param2": {"type": "integer", "description": "Description of parameter 2"}
        },
        "required": ["param1"]
    }
}
```

2. Implement the tool function in `agent_loop.py` as a method of the `AgentLoop` class:
```python
def my_new_tool(self, param1: str, param2: int = 0) -> List[Dict]:
    # Tool implementation
    result = f"Processed {param1} with {param2}"
    return [
        {
            "type": "text",
            "text": result
        }
    ]
```

3. Register the tool in the conversation handler:
```python
completion_res = self.handle_conversation(
    conversation_history=conversation_history,
    system=SystemPromptDefinitions.MAIN_AGENT_LOOP,
    tools=[deep_iterattive_web_search_tool, my_new_tool]
)
```

## License

MIT