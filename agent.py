import os
from openai import OpenAI
from pdf_processor import query_chroma
from mcp_server import MCPTavilyServer
from dotenv import load_dotenv

load_dotenv()

class OpenAIAgent:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.mcp_server = MCPTavilyServer()
        self.conversation_memory = {}
    
    def check_guardrails(self, user_query):
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
    
    def needs_web_search(self, query):
        """Determine if query needs real-time web search"""
        web_keywords = [
            'weather', 'today', 'current', 'now', 'latest', 'recent', 'news', 
            'stock price', 'live', 'temperature', 'forecast', 'today\'s',
            'what\'s happening', 'breaking news', 'current events'
        ]
        return any(keyword in query.lower() for keyword in web_keywords)
    
    def evaluate_rag_sufficiency(self, query, rag_results):
        """Evaluate if RAG results are sufficient for the query"""
        if not rag_results:
            return False, "No relevant documents found"
        
        # If query needs real-time info, RAG is insufficient
        if self.needs_web_search(query):
            return False, "Query requires real-time information"
        
        # Check content relevance with keyword matching
        query_lower = query.lower()
        query_keywords = [word for word in query_lower.split() if len(word) > 2]
        
        combined_content = ' '.join(rag_results[:2]).lower()
        
        # Need at least 2 matching keywords for relevance
        matches = sum(1 for keyword in query_keywords if keyword in combined_content)
        if matches < 2:
            return False, "RAG content not relevant to query"
        
        # Check minimum content length
        if len(combined_content.strip()) < 100:
            return False, "Insufficient content length"
        
        return True, "Sufficient document content found"
    
    def process_query(self, user_query, session_id="default"):
        # Initialize session memory
        if session_id not in self.conversation_memory:
            self.conversation_memory[session_id] = []
        
        # Check guardrails first
        is_inappropriate, guardrail_message = self.check_guardrails(user_query)
        if is_inappropriate:
            return guardrail_message
        
        # Step 1: Always try RAG first
        rag_results = query_chroma(user_query)
        is_sufficient, eval_reason = self.evaluate_rag_sufficiency(user_query, rag_results)
        
        context_parts = []
        sources = []
        
        # Step 2: Use web search if RAG insufficient OR query needs real-time info
        if not is_sufficient or self.needs_web_search(user_query):
            print(f"Using web search because: {eval_reason}")  # Debug log
            web_results = self.mcp_server.search_web(user_query)
            if web_results:
                web_content = "\n".join([r.get('content', '')[:800] for r in web_results[:3] if r.get('content')])
                if web_content.strip():
                    context_parts.append("Current web information: " + web_content)
                    sources.append("web search")
        
        # Add RAG results only if they're relevant and sufficient
        if rag_results and is_sufficient and not self.needs_web_search(user_query):
            context_parts.append("Document context: " + "\n".join(rag_results[:2]))
            sources.append("documents")
        
        # Prepare conversation context
        memory_context = ""
        if self.conversation_memory[session_id]:
            recent_history = self.conversation_memory[session_id][-2:]  # Last exchange
            memory_context = "Previous conversation:\n" + "\n".join([
                f"User: {h['user']}\nAssistant: {h['assistant']}" for h in recent_history
            ]) + "\n\n"
        
        # Generate response
        system_prompt = f"""You are a helpful assistant with access to both documents and real-time web search. 
Sources available: {', '.join(sources) if sources else 'general knowledge'}

Guidelines:
1. If web search data is provided, prioritize it for current/real-time information
2. If document context is provided, use it for factual information from documents
3. If no relevant context is available, clearly state you need to search for information
4. Always provide helpful responses and suggest alternatives when information is limited
5. Be concise but comprehensive
6. Answer in the same language as the user's question"""
        
        full_context = memory_context + "\n".join(context_parts) if context_parts else memory_context + "No specific context available."
        
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context: {full_context}\n\nQuestion: {user_query}"}
            ],
            max_tokens=600
        )
        
        assistant_response = response.choices[0].message.content
        
        # Update conversation memory
        self.conversation_memory[session_id].append({
            "user": user_query,
            "assistant": assistant_response
        })
        
        # Keep only last 6 exchanges
        if len(self.conversation_memory[session_id]) > 6:
            self.conversation_memory[session_id] = self.conversation_memory[session_id][-6:]
        
        return assistant_response
