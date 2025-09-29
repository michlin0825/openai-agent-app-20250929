import os
import nest_asyncio
from typing import Optional, Tuple
from agents import Agent, Runner
from openai import OpenAI
from pdf_processor import query_chroma
from mcp_server import MCPTavilyServer
from memory_manager import MemoryManager
from guardrails import GuardrailsManager
from dotenv import load_dotenv

# Enable nested event loops
nest_asyncio.apply()

load_dotenv()

class OpenAIAgentSDK:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.mcp_server = MCPTavilyServer()
        
        # Initialize memory and guardrails managers
        self.memory_manager = MemoryManager(self.client)
        self.guardrails_manager = GuardrailsManager(self.client)
        
        # Initialize OpenAI Agent SDK (tools handled separately due to SDK limitations)
        self.agent = Agent(
            name="RAG-Web-Search-Agent",
            model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
            instructions="""You are an intelligent research assistant with autonomous reasoning capabilities that combines document knowledge with real-time web search.

For each query:
1. Analyze if you need current information (web search for recent events, prices, news)
2. Check if domain knowledge is needed (document search for stored information)
3. For complex topics, use BOTH sources to cross-validate and provide comprehensive answers
4. Think step-by-step and explain your reasoning process
5. Maintain conversation context and apply content safety guardrails

Your capabilities:
- Answer questions using your knowledge base
- Search real-time web information when needed
- Cross-reference multiple sources for accuracy
- Maintain conversation memory across exchanges
- Filter inappropriate content automatically

Always be thorough but concise. Use multiple information sources when beneficial to provide well-researched, accurate responses."""
        )
    
    def search_documents_tool(self, query: str) -> str:
        """Search ChromaDB for document information"""
        try:
            results = query_chroma(query)
            if results and len(results) > 0:
                return f"Document search results: {results}"
            return "No relevant documents found."
        except Exception as e:
            return f"Document search error: {str(e)}"
    
    def search_web_tool(self, query: str) -> str:
        """Search the web for current information"""
        try:
            results = self.mcp_server.search_web(query, max_results=int(os.getenv("MAX_SEARCH_RESULTS", "3")))
            if results:
                formatted_results = []
                for result in results:
                    formatted_results.append(f"Title: {result.get('title', 'N/A')}\nContent: {result.get('content', 'N/A')}\nURL: {result.get('url', 'N/A')}")
                return f"Web search results:\n\n" + "\n\n".join(formatted_results)
            return "No web search results found."
        except Exception as e:
            return f"Web search error: {str(e)}"
    
    def check_guardrails(self, user_query: str) -> Tuple[bool, Optional[str]]:
        """Check content safety guardrails"""
        return self.guardrails_manager.check_guardrails(user_query)
    
    def needs_web_search(self, query: str) -> bool:
        """Check if query needs web search"""
        web_keywords = ['weather', 'news', 'current', 'today', 'latest', 'stock price', 'happening now', 'temperature', 'forecast']
        return any(keyword in query.lower() for keyword in web_keywords)
    
    def needs_document_search(self, query: str) -> bool:
        """Check if query needs document search"""
        doc_keywords = ['amazon', 'aws', 'shareholder', 'financial', 'revenue', 'business', 'profit', 'earnings', 'annual report']
        return any(keyword in query.lower() for keyword in doc_keywords)
    
    async def stream_response_async(self, user_query: str, session_id: str):
        """Stream response using OpenAI Agents SDK with intelligent tool routing"""
        
        # Check guardrails first
        is_blocked, guardrail_message = self.check_guardrails(user_query)
        if is_blocked:
            yield guardrail_message
            return
        
        # Get conversation memory
        memory_context = self.memory_manager.get_memory_context(session_id)
        
        # Prepare context with memory
        full_query = f"Previous conversation context: {memory_context}\n\nCurrent query: {user_query}"
        
        full_response = ""
        
        try:
            # Intelligent tool routing with streaming
            if self.needs_web_search(user_query):
                # Use web search tool and stream formatted response
                web_results = self.search_web_tool(user_query)
                format_prompt = f"User asked: {user_query}\n\nWeb search results: {web_results}\n\nPlease provide a natural, helpful response based on this information."
                
                # Stream the formatted response
                async for chunk in self._stream_openai_response(format_prompt):
                    full_response += chunk
                    yield chunk
                    
            elif self.needs_document_search(user_query):
                # Use document search tool and stream formatted response
                doc_results = self.search_documents_tool(user_query)
                format_prompt = f"User asked: {user_query}\n\nDocument search results: {doc_results}\n\nPlease provide a natural, helpful response based on this information."
                
                # Stream the formatted response
                async for chunk in self._stream_openai_response(format_prompt):
                    full_response += chunk
                    yield chunk
                    
            else:
                # Stream general query response
                async for chunk in self._stream_openai_response(full_query):
                    full_response += chunk
                    yield chunk
            
            # Update conversation memory with full response
            self.memory_manager.update_memory(session_id, user_query, full_response)
            
        except Exception as e:
            error_msg = f"I encountered an error processing your request: {str(e)}"
            yield error_msg
            self.memory_manager.update_memory(session_id, user_query, error_msg)
    
    async def _stream_openai_response(self, prompt: str):
        """Stream response from OpenAI using direct client"""
        try:
            stream = self.client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            yield f"Streaming error: {str(e)}"
                    
    async def process_query_async(self, user_query: str, session_id: str) -> str:
        """Process query using hybrid approach with intelligent tool routing"""
        
        # Check guardrails first
        is_blocked, guardrail_message = self.check_guardrails(user_query)
        if is_blocked:
            return guardrail_message
        
        # Get conversation memory
        memory_context = self.memory_manager.get_memory_context(session_id)
        
        # Prepare context with memory
        full_query = f"Previous conversation context: {memory_context}\n\nCurrent query: {user_query}"
        
        try:
            # Intelligent tool routing
            if self.needs_web_search(user_query):
                # Use web search tool and format with OpenAI
                web_results = self.search_web_tool(user_query)
                format_prompt = f"User asked: {user_query}\n\nWeb search results: {web_results}\n\nPlease provide a natural, helpful response based on this information."
                result = Runner.run_sync(self.agent, format_prompt)
                response = result.final_output or "I found some information but couldn't format it properly."
                
            elif self.needs_document_search(user_query):
                # Use document search tool and format with OpenAI
                doc_results = self.search_documents_tool(user_query)
                format_prompt = f"User asked: {user_query}\n\nDocument search results: {doc_results}\n\nPlease provide a natural, helpful response based on this information."
                result = Runner.run_sync(self.agent, format_prompt)
                response = result.final_output or "I found some information but couldn't format it properly."
                
            else:
                # Use OpenAI Agents SDK for general queries
                result = Runner.run_sync(self.agent, full_query)
                response = result.final_output or "I apologize, but I couldn't generate a response."
            
            # Update conversation memory
            self.memory_manager.update_memory(session_id, user_query, response)
            
            return response
            
        except Exception as e:
            return f"I encountered an error processing your request: {str(e)}"
