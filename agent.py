import os
import asyncio
import nest_asyncio
from typing import Dict, List, Optional, Tuple
from agents import Agent, Runner
from openai import OpenAI
from pdf_processor import query_chroma
from mcp_server import MCPTavilyServer
from dotenv import load_dotenv

# Enable nested event loops
nest_asyncio.apply()

load_dotenv()

def search_documents(query: str) -> str:
    """Search ChromaDB for document information"""
    try:
        results = query_chroma(query)
        if results and len(results) > 0:
            return f"Document search results: {results}"
        return "No relevant documents found."
    except Exception as e:
        return f"Document search error: {str(e)}"

# Add required attributes for OpenAI Agents SDK
search_documents.__name__ = "search_documents"

def search_web(query: str) -> str:
    """Search the web for current information"""
    try:
        mcp_server = MCPTavilyServer()
        results = mcp_server.search_web(query, max_results=3)
        if results:
            formatted_results = []
            for result in results:
                formatted_results.append(f"Title: {result.get('title', 'N/A')}\nContent: {result.get('content', 'N/A')}\nURL: {result.get('url', 'N/A')}")
            return f"Web search results:\n\n" + "\n\n".join(formatted_results)
        return "No web search results found."
    except Exception as e:
        return f"Web search error: {str(e)}"

# Add required attributes for OpenAI Agents SDK  
search_web.__name__ = "search_web"

class OpenAIAgentSDK:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.conversation_memory = {}
        
        # Initialize OpenAI Agent SDK (tools will be added later when needed)
        self.agent = Agent(
            name="RAG-Web-Search-Agent",
            model="gpt-3.5-turbo",
            instructions="""You are an intelligent assistant that combines document knowledge with real-time web search.
            
            Your capabilities:
            1. Answer questions using your knowledge
            2. Maintain conversation context
            3. Apply content safety guardrails
            
            Provide helpful and informative responses."""
        )
    
    def check_guardrails(self, user_query: str) -> Tuple[bool, Optional[str]]:
        """Enhanced guardrails for inappropriate content and Taiwan politics"""
        query_lower = user_query.lower()
        
        # Taiwan politics keywords
        taiwan_politics_keywords = [
            'taiwan politics', 'taiwanese politics', 'taiwan election', 'taiwan government',
            'dpp', 'kmt', 'taiwan independence', 'taiwan unification', 'cross-strait',
            'taiwan china', 'taiwan president', 'taiwan democracy', 'taiwan party',
            'pan-blue', 'pan-green', 'taiwan political', 'taiwan vote', 'taiwan campaign'
        ]
        
        # Check for Taiwan politics
        if any(keyword in query_lower for keyword in taiwan_politics_keywords):
            return True, "I appreciate your interest in current affairs! However, I'm designed to focus on helpful, informative topics rather than political discussions. I'd be happy to help you with questions about technology, business, weather, or other topics. What else can I assist you with? 😊"
        
        # Check OpenAI moderation for abusive content
        try:
            moderation = self.client.moderations.create(input=user_query)
            result = moderation.results[0]
            
            if result.flagged:
                return True, "I understand you're looking for information, but I'm designed to have respectful, helpful conversations. Could we explore something else I can assist you with today? 😊"
            return False, None
        except:
            return False, None
    
    async def process_query_async(self, user_query: str, session_id: str) -> str:
        """Process query using OpenAI Agents SDK with async support"""
        
        # Check guardrails first
        is_blocked, guardrail_message = self.check_guardrails(user_query)
        if is_blocked:
            return guardrail_message
        
        # Get conversation memory
        memory_context = self.get_memory_context(session_id)
        
        # Prepare context with memory
        full_query = f"Previous conversation context: {memory_context}\n\nCurrent query: {user_query}"
        
        try:
            # Check if query needs web search or document search
            if self.needs_web_search(user_query):
                web_results = search_web(user_query)
                response = f"Based on web search: {web_results}"
            elif self.needs_document_search(user_query):
                doc_results = search_documents(user_query)
                response = f"Based on documents: {doc_results}"
            else:
                # Use OpenAI Agents SDK for general queries
                result = Runner.run_sync(self.agent, full_query)
                response = result.final_output or "I apologize, but I couldn't generate a response."
            
            # Update conversation memory
            self.update_memory(session_id, user_query, response)
            
            return response
            
        except Exception as e:
            return f"I encountered an error processing your request: {str(e)}"
    
    def needs_web_search(self, query: str) -> bool:
        """Check if query needs web search"""
        web_keywords = ['weather', 'news', 'current', 'today', 'latest', 'stock price', 'happening now']
        return any(keyword in query.lower() for keyword in web_keywords)
    
    def needs_document_search(self, query: str) -> bool:
        """Check if query needs document search"""
        doc_keywords = ['amazon', 'aws', 'shareholder', 'financial', 'revenue', 'business']
        return any(keyword in query.lower() for keyword in doc_keywords)
    
    def process_query(self, user_query: str, session_id: str) -> str:
        """Synchronous wrapper for async process_query"""
        return asyncio.run(self.process_query_async(user_query, session_id))
    
    def get_memory_context(self, session_id: str) -> str:
        """Get conversation memory for session"""
        if session_id not in self.conversation_memory:
            return "No previous conversation."
        
        memory = self.conversation_memory[session_id]
        context_parts = []
        
        for exchange in memory[-3:]:  # Last 3 exchanges
            context_parts.append(f"User: {exchange['user']}")
            context_parts.append(f"Assistant: {exchange['assistant']}")
        
        return "\n".join(context_parts)
    
    def update_memory(self, session_id: str, user_query: str, response: str):
        """Update conversation memory"""
        if session_id not in self.conversation_memory:
            self.conversation_memory[session_id] = []
        
        self.conversation_memory[session_id].append({
            'user': user_query,
            'assistant': response
        })
        
        # Keep only last 6 exchanges
        if len(self.conversation_memory[session_id]) > 6:
            self.conversation_memory[session_id] = self.conversation_memory[session_id][-6:]

# Main agent class for the application
OpenAIAgent = OpenAIAgentSDK
