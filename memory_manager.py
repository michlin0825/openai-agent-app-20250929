"""
Memory Management Module for OpenAI Agent App
Handles conversation memory, context retrieval, and automatic compaction
"""

import os
import time
from typing import Dict, List, Optional
from openai import OpenAI


class MemoryManager:
    def __init__(self, openai_client: OpenAI):
        self.client = openai_client
        self.conversation_memory: Dict[str, List[Dict]] = {}
        self.max_exchanges = int(os.getenv("MAX_EXCHANGES", "20"))  # Maximum exchanges before compaction
        self.keep_recent = int(os.getenv("KEEP_RECENT_EXCHANGES", "5"))     # Recent exchanges to keep after compaction
    
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
        """Update conversation memory with automatic summarization"""
        if session_id not in self.conversation_memory:
            self.conversation_memory[session_id] = []
        
        self.conversation_memory[session_id].append({
            'user': user_query,
            'assistant': response,
            'timestamp': time.time()
        })
        
        # When reaching max exchanges, summarize and compact
        if len(self.conversation_memory[session_id]) >= self.max_exchanges:
            self._compact_memory(session_id)
    
    def _compact_memory(self, session_id: str):
        """Compact memory by summarizing older conversations"""
        memory = self.conversation_memory[session_id]
        
        # Take older exchanges for summarization, keep recent ones
        old_conversations = memory[:-self.keep_recent]
        recent_conversations = memory[-self.keep_recent:]
        
        # Create summary of old conversations
        conversation_text = ""
        for exchange in old_conversations:
            conversation_text += f"User: {exchange['user']}\nAssistant: {exchange['assistant']}\n\n"
        
        try:
            # Use OpenAI to summarize
            summary_response = self.client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
                messages=[{
                    "role": "user", 
                    "content": f"Please provide a concise summary of this conversation history, focusing on key topics discussed and important information shared:\n\n{conversation_text}"
                }],
                max_tokens=int(os.getenv("SUMMARIZATION_MAX_TOKENS", "200"))
            )
            
            summary = summary_response.choices[0].message.content
            
            # Replace old conversations with summary
            self.conversation_memory[session_id] = [
                {
                    'user': '[Previous conversation summary]', 
                    'assistant': summary,
                    'timestamp': time.time()
                }
            ] + recent_conversations
            
        except Exception as e:
            print(f"Memory compaction error: {e}")
            # Fallback: just keep recent conversations
            self.conversation_memory[session_id] = recent_conversations
    
    def clear_session_memory(self, session_id: str):
        """Clear memory for a specific session"""
        if session_id in self.conversation_memory:
            del self.conversation_memory[session_id]
    
    def get_session_stats(self, session_id: str) -> Dict:
        """Get statistics for a session's memory"""
        if session_id not in self.conversation_memory:
            return {"exchanges": 0, "total_tokens_estimate": 0}
        
        memory = self.conversation_memory[session_id]
        total_chars = sum(len(ex['user']) + len(ex['assistant']) for ex in memory)
        
        return {
            "exchanges": len(memory),
            "total_chars": total_chars,
            "estimated_tokens": total_chars // 4  # Rough estimate
        }
