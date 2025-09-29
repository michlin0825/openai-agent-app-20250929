import chainlit as cl
import os
from dotenv import load_dotenv
from agent import OpenAIAgentSDK

load_dotenv()

# Initialize agent with OpenAI Agents SDK
agent = OpenAIAgentSDK()

@cl.password_auth_callback
def auth_callback(username: str, password: str):
    if username == os.getenv("CHAINLIT_USERNAME") and password == os.getenv("CHAINLIT_PASSWORD"):
        return cl.User(identifier="admin", metadata={"role": "admin"})
    return None

@cl.on_chat_start
async def start():
    # Initialize session
    cl.user_session.set("session_id", cl.user_session.get("id"))
    await cl.Message(content="👋 Welcome! I'm your AI assistant powered by the OpenAI Agents SDK. I can help you with questions about documents or current information through web search. What would you like to know?").send()

@cl.on_message
async def main(message: cl.Message):
    session_id = cl.user_session.get("session_id", "default")
    
    # Create empty message for streaming
    msg = cl.Message(content="")
    await msg.send()
    
    try:
        # Stream response in real-time
        full_response = ""
        async for chunk in agent.stream_response_async(message.content, session_id):
            full_response += chunk
            await msg.stream_token(chunk)
        
        # Update final message
        await msg.update()
        
    except Exception as e:
        error_msg = f"I encountered an error: {str(e)}"
        await msg.stream_token(error_msg)
        await msg.update()
