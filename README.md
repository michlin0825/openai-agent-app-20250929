# OpenAI Agent App with RAG & Web Search

## What This App Does

This intelligent chatbot combines **document knowledge** with **real-time web search** to provide comprehensive answers. Built using the **OpenAI Agents SDK**, it demonstrates modern agentic AI capabilities with RAG-first architecture and hybrid search functionality.

### Screenshots

**App Login Screen:**
![Chat Interface](screenshots/screenshot_1.png)

**Q&A in Action:**
![Web Search Results](screenshots/screenshot_2.png)

### Use Cases
- **Document Q&A**: Ask questions about uploaded PDFs (currently contains Amazon 2023 Shareholder Letter)
- **Current Information**: Get real-time data like weather, news, or stock prices
- **Hybrid Queries**: Combine document facts with current context
- **Conversational Memory**: Follow-up questions that reference previous exchanges
- **Content Safety**: Built-in guardrails for inappropriate or sensitive topics

---

## Tech Stack

### **Core Framework**
- **Python 3.x** + **Chainlit** - Chat interface framework
- **OpenAI Agents SDK** - Official agentic AI framework with built-in tracing and async support
- **OpenAI GPT-3.5-turbo** - Language model with moderation API

### **Data & Search**
- **ChromaDB** - Vector database for document storage and retrieval
- **Tavily API** - Real-time web search for current information
- **PyPDF2** - PDF document processing
- **nest-asyncio** - Nested event loop support for async processing

### **Architecture**
- **Intelligent Tool Routing** - Automatic detection and routing between document search, web search, and general queries
- **Enhanced Keyword Detection** - Expanded patterns for better query classification
- **Polished Response Formatting** - Natural language processing of search results
- **Session Memory** - Conversation context management
- **JWT Authentication** - Secure user sessions
- **Async Event Loop** - Non-blocking processing with nest-asyncio

---

## Quick Start
```bash
cd /Users/mba/Desktop/openai-agent-app-20250929
cp .env.example .env
# Edit .env with your API keys
source venv/bin/activate
chainlit run app.py --port 8000
```
Access at `http://localhost:8000` with credentials from `.env` file.

**Note**: If you encounter Chainlit compatibility issues with Python 3.13, the app requires Chainlit 2.8.0+ which is already specified in requirements.txt.

### Try These Sample Questions

**Document-Based Queries** (searches Amazon 2023 Shareholder Letter):
- *"What did Amazon say about AI in 2023?"*
  - Expected: Detailed response about Amazon's AI initiatives from the shareholder letter
- *"How did Amazon perform financially in 2023?"*
  - Expected: Revenue, profit, and growth metrics from the document
- *"What are Amazon's key business segments?"*
  - Expected: AWS, retail, advertising breakdown from shareholder data

**Real-Time Web Search** (triggers Tavily search):
- *"What's the weather in New York today?"*
  - Expected: Current weather conditions and forecast
- *"What's Amazon's current stock price?"*
  - Expected: Live AMZN stock price and recent performance
- *"What's happening in tech news today?"*
  - Expected: Recent technology news and developments
- *"What's the temperature in Tokyo?"*
  - Expected: Current temperature and weather conditions

**Conversational Memory** (references previous exchanges):
- First: *"Tell me about Amazon's AWS business"*
- Follow-up: *"How does that compare to their retail segment?"*
  - Expected: Comparative analysis referencing the previous AWS discussion
- Follow-up: *"What did you just tell me about revenue?"*
  - Expected: Summary of previously mentioned revenue figures

**Content Safety** (tests guardrails):
- *"What do you think about Taiwan politics?"*
  - Expected: Polite deflection with alternative topic suggestions

**Guardrails Verification**: ✅ Tested and working - Taiwan politics filtering active with polite responses.

---

## Features
- **OpenAI Agents SDK Integration**: Official agent framework with built-in tracing and async processing
- **Intelligent Tool Routing**: Automatic detection and routing between document search, web search, and general queries
- **Enhanced Keyword Detection**: Expanded patterns for weather, news, financial, and document queries
- **Polished Response Formatting**: Natural language processing of search results for human-readable answers
- **Async Processing**: Non-blocking query processing with visual indicators using nest-asyncio
- **Built-in Tracing**: OpenAI Agents SDK provides automatic execution tracing
- **Multi-turn Memory**: Session-based conversation history (6 exchanges max)
- **Content Guardrails**: Taiwan politics filtering + OpenAI moderation
- **Real-time Web Search**: Tavily integration for current information (weather, news, stock prices)
- **Document Search**: ChromaDB vector search for uploaded PDFs (Amazon 2023 Shareholder Letter)
- **Chainlit UI**: Web interface with authentication and OpenAI logo
- **Persistent Storage**: ChromaDB maintains documents between sessions

## Document Management
**Existing documents are preserved** - no need to re-ingest on startup.

To add new documents:
```bash
python ingest_documents.py path/to/new_document.pdf
```

## Configuration
Create a `.env` file from the example:
```bash
cp .env.example .env
```

Then fill in your actual API keys:
- `OPENAI_API_KEY` - Your OpenAI API key
- `TAVILY_API_KEY` - Your Tavily search API key  
- `CHAINLIT_AUTH_SECRET` - JWT secret for authentication
- `CHAINLIT_USERNAME` - Login username
- `CHAINLIT_PASSWORD` - Login password

## Installation
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Guardrails Testing
Create a test script to verify guardrails:
```python
from agent import OpenAIAgent
agent = OpenAIAgent()
is_blocked, msg = agent.check_guardrails("What about Taiwan politics?")
print("Blocked:" if is_blocked else "Allowed:", msg)
```
Expected: Taiwan politics queries blocked, normal queries allowed.

## Recent Improvements (20250929)
- ✅ **OpenAI Agents SDK Integration**: Migrated from custom agent to official OpenAI Agents SDK
- ✅ **Fixed Tools Integration**: Resolved function attribute issues with intelligent tool routing
- ✅ **Nested Event Loop Fix**: Resolved async issues with nest-asyncio
- ✅ **Intelligent Tool Routing**: Automatic detection and routing between document search, web search, and general queries
- ✅ **Polished Responses**: Natural language formatting of search results using OpenAI
- ✅ **Enhanced Keyword Detection**: Expanded patterns for better query classification
- ✅ **Async Processing**: Non-blocking query processing with visual indicators
- ✅ **Built-in Tracing**: Automatic execution tracing from OpenAI Agents SDK
- ✅ **Enhanced UI**: Processing indicators and step-by-step execution visibility
- ✅ **Code Cleanup**: Removed interim artifacts and consolidated to final implementation

---

## License
MIT License - Feel free to use and modify for your projects!
