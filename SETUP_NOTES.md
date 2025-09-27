# Setup Notes - OpenAI Agent App 20250929

## Dependency Resolution History

### Issue: Python 3.13 + Chainlit Compatibility
**Problem**: Chainlit 1.1.304 has Pydantic compatibility issues with Python 3.13
```
PydanticUserError: `CodeSettings` is not fully defined
```

**Solution**: Upgrade to Chainlit 2.8.0+
```bash
pip install "chainlit>=2.8.0" --upgrade
```

### Working Configuration
- **Python**: 3.13
- **Chainlit**: 2.8.1 (minimum 2.8.0)
- **OpenAI**: 1.109.1+
- **ChromaDB**: 1.1.0+

### Verified Working Dependencies
```
chainlit>=2.8.0
openai>=1.54.3
chromadb>=0.5.15
python-dotenv>=1.0.1
PyPDF2>=3.0.1
tavily-python>=0.5.0
```

## Environment Setup
1. Create virtual environment: `python3 -m venv venv`
2. Activate: `source venv/bin/activate`
3. Install: `pip install -r requirements.txt`
4. Configure environment: `cp .env.example .env` and add your API keys
5. Run: `chainlit run app.py --port 8000`

## Testing Checklist
- [ ] Guardrails working: Create test script to verify Taiwan politics filtering
- [ ] Full agent processing: Test RAG and web search functionality  
- [ ] ChromaDB persistence: Check `chroma_db/` directory exists
- [ ] Web interface: Access `http://localhost:8000`
- [ ] Authentication: Login with credentials from `.env`

## Known Issues Resolved
- ✅ Python 3.13 Pydantic compatibility
- ✅ Chainlit version conflicts
- ✅ Taiwan politics guardrails
- ✅ RAG evaluation accuracy
- ✅ Web search activation logic
- ✅ Environment variable configuration
- ✅ ChromaDB persistence between sessions
