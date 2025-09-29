"""
Guardrails Module for OpenAI Agent App
Handles content safety, moderation, and topic filtering
"""

from typing import Tuple, Optional
from openai import OpenAI


class GuardrailsManager:
    def __init__(self, openai_client: OpenAI):
        self.client = openai_client
        
        # Taiwan politics keywords for filtering
        self.taiwan_politics_keywords = [
            'taiwan politics', 'taiwanese politics', 'taiwan election', 'taiwan government',
            'dpp', 'kmt', 'taiwan independence', 'taiwan unification', 'cross-strait',
            'taiwan china', 'taiwan president', 'taiwan democracy', 'taiwan party',
            'pan-blue', 'pan-green', 'taiwan political', 'taiwan vote', 'taiwan campaign'
        ]
        
        # Polite response for blocked content
        self.blocked_response = (
            "I appreciate your interest in current affairs! However, I'm designed to focus on "
            "helpful, informative topics rather than political discussions. I'd be happy to help "
            "you with questions about technology, business, weather, or other topics. "
            "What else can I assist you with? 😊"
        )
        
        self.moderation_response = (
            "I understand you're looking for information, but I'm designed to have respectful, "
            "helpful conversations. Could we explore something else I can assist you with today? 😊"
        )
    
    def check_guardrails(self, user_query: str) -> Tuple[bool, Optional[str]]:
        """
        Enhanced guardrails for inappropriate content and Taiwan politics
        
        Returns:
            Tuple[bool, Optional[str]]: (is_blocked, response_message)
        """
        query_lower = user_query.lower()
        
        # Check for Taiwan politics
        if self._contains_taiwan_politics(query_lower):
            return True, self.blocked_response
        
        # Check OpenAI moderation for abusive content
        if self._check_openai_moderation(user_query):
            return True, self.moderation_response
        
        return False, None
    
    def _contains_taiwan_politics(self, query_lower: str) -> bool:
        """Check if query contains Taiwan politics keywords"""
        return any(keyword in query_lower for keyword in self.taiwan_politics_keywords)
    
    def _check_openai_moderation(self, user_query: str) -> bool:
        """Check OpenAI moderation API for inappropriate content"""
        try:
            moderation = self.client.moderations.create(input=user_query)
            result = moderation.results[0]
            return result.flagged
        except Exception as e:
            print(f"Moderation API error: {e}")
            return False  # Allow if moderation fails
