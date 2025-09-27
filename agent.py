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

class OpenAIAgentSDK:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.mcp_server = MCPTavilyServer()
        self.conversation_memory = {}
        
        # Initialize OpenAI Agent SDK (tools handled separately due to SDK limitations)
        self.agent = Agent(
            name="RAG-Web-Search-Agent",
            model="gpt-3.5-turbo",
            instructions="""You are an intelligent assistant that combines document knowledge with real-time web search.
            
            Your capabilities:
            1. Answer questions using your knowledge
            2. Maintain conversation context
            3. Apply content safety guardrails
            
            Provide helpful and informative responses. When you need specific current information or document details, indicate what type of search would be helpful."""
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
            results = self.mcp_server.search_web(query, max_results=3)
            if results:
                formatted_results = []
                for result in results:
                    formatted_results.append(f"Title: {result.get('title', 'N/A')}\nContent: {result.get('content', 'N/A')}\nURL: {result.get('url', 'N/A')}")
                return f"Web search results:\n\n" + "\n\n".join(formatted_results)
            return "No web search results found."
        except Exception as e:
            return f"Web search error: {str(e)}"
    
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
        memory_context = self.get_memory_context(session_id)
        
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
            self.update_memory(session_id, user_query, full_response)
            
        except Exception as e:
            error_msg = f"I encountered an error processing your request: {str(e)}"
            yield error_msg
            self.update_memory(session_id, user_query, error_msg)
    
    async def _stream_openai_response(self, prompt: str):
        """Stream response from OpenAI using direct client"""
        try:
            stream = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
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
        memory_context = self.get_memory_context(session_id)
        
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
            self.update_memory(session_id, user_query, response)
            
            return response
            
        except Exception as e:
            return f"I encountered an error processing your request: {str(e)}"
    
    def process_query(self, user_query: str, session_id: str) -> str:
        """Synchronous wrapper for async process_query"""
        return asyncio.run(self.process_query_async(user_query, session_id))
    
    def get_memory_context(self, session_id: str) -> str:
        """Get conversation memory for session"""
        if session_id not in self.conversation_memory:
            return "No previous conversation."
        
        memory = self.conversation_memory[session_id]
        context_parts = []
        
        # Use last 10 exchanges (20 turns) for better context
        for exchange in memory[-10:]:
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
        
        # Keep last 20 exchanges (40 turns total)
        if len(self.conversation_memory[session_id]) > 20:
            self.conversation_memory[session_id] = self.conversation_memory[session_id][-20:]

# Main agent class for the application
OpenAIAgent = OpenAIAgentSDK
