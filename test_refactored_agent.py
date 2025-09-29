#!/usr/bin/env python3
"""
Test script for refactored OpenAI Agent App
Tests memory management and guardrails functionality
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_agent_initialization():
    """Test that the agent initializes correctly with new modules"""
    try:
        from agent import OpenAIAgentSDK
        agent = OpenAIAgentSDK()
        print("✅ Agent initialization successful")
        
        # Test that modules are properly initialized
        assert hasattr(agent, 'memory_manager'), "Memory manager not initialized"
        assert hasattr(agent, 'guardrails_manager'), "Guardrails manager not initialized"
        print("✅ Memory and guardrails managers initialized")
        
        return agent
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        return None

def test_guardrails(agent):
    """Test guardrails functionality"""
    print("\n🔒 Testing Guardrails...")
    
    # Test blocked content (Taiwan politics)
    test_queries = [
        ("Tell me about Taiwan politics", True),  # Should be blocked
        ("What's the weather like today?", False),  # Should pass
        ("Taiwan independence movement", True),  # Should be blocked
        ("How does machine learning work?", False)  # Should pass
    ]
    
    for query, should_be_blocked in test_queries:
        is_blocked, response = agent.check_guardrails(query)
        
        if is_blocked == should_be_blocked:
            status = "✅"
        else:
            status = "❌"
        
        print(f"{status} Query: '{query}' - Blocked: {is_blocked}")
        if is_blocked:
            print(f"   Response: {response[:100]}...")

def test_memory_management(agent):
    """Test memory management functionality"""
    print("\n🧠 Testing Memory Management...")
    
    session_id = "test_session"
    
    # Test initial memory state
    context = agent.memory_manager.get_memory_context(session_id)
    assert context == "No previous conversation.", f"Expected empty memory, got: {context}"
    print("✅ Initial memory state correct")
    
    # Test memory updates
    agent.memory_manager.update_memory(session_id, "Hello", "Hi there!")
    agent.memory_manager.update_memory(session_id, "How are you?", "I'm doing well, thanks!")
    
    context = agent.memory_manager.get_memory_context(session_id)
    assert "Hello" in context and "Hi there!" in context, "Memory not storing correctly"
    print("✅ Memory storage working")
    
    # Test memory stats
    stats = agent.memory_manager.get_session_stats(session_id)
    assert stats["exchanges"] == 2, f"Expected 2 exchanges, got {stats['exchanges']}"
    print("✅ Memory statistics working")
    
    # Test memory clearing
    agent.memory_manager.clear_session_memory(session_id)
    context = agent.memory_manager.get_memory_context(session_id)
    assert context == "No previous conversation.", "Memory not cleared properly"
    print("✅ Memory clearing working")

def test_tool_routing(agent):
    """Test intelligent tool routing"""
    print("\n🔧 Testing Tool Routing...")
    
    # Test web search detection
    web_queries = ["What's the weather today?", "Latest news about AI", "Current stock price"]
    for query in web_queries:
        needs_web = agent.needs_web_search(query)
        print(f"{'✅' if needs_web else '❌'} Web search for: '{query}' - Detected: {needs_web}")
    
    # Test document search detection
    doc_queries = ["What did Amazon say about AI?", "Amazon revenue 2023", "AWS financial results"]
    for query in doc_queries:
        needs_doc = agent.needs_document_search(query)
        print(f"{'✅' if needs_doc else '❌'} Doc search for: '{query}' - Detected: {needs_doc}")

def main():
    """Run all tests"""
    print("🧪 Testing Refactored OpenAI Agent App\n")
    
    # Check environment variables
    required_vars = ["OPENAI_API_KEY", "TAVILY_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        print("Please check your .env file")
        return
    
    # Test agent initialization
    agent = test_agent_initialization()
    if not agent:
        return
    
    # Run tests
    test_guardrails(agent)
    test_memory_management(agent)
    test_tool_routing(agent)
    
    print("\n🎉 All tests completed!")
    print("\nRefactored modules:")
    print("  📁 memory_manager.py - Handles conversation memory and compaction")
    print("  📁 guardrails.py - Handles content safety and moderation")
    print("  📁 agent.py - Main agent logic (refactored to use modules)")

if __name__ == "__main__":
    main()
