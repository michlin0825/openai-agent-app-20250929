import chainlit as cl
import os
from dotenv import load_dotenv
from agent import OpenAIAgent

load_dotenv()

# Initialize agent with OpenAI Agents SDK
agent = OpenAIAgent()

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
    
    # Show processing indicator with tracing
    async with cl.Step(name="🤖 Agent Processing", type="run") as step:
        step.output = "Analyzing query and determining best information sources..."
        
        try:
            # Use async processing with OpenAI Agents SDK
            response = await agent.process_query_async(message.content, session_id)
            step.output = "✅ Query processed successfully with OpenAI Agents SDK"
        except Exception as e:
            response = f"I encountered an error: {str(e)}"
            step.output = f"❌ Error: {str(e)}"
    
    await cl.Message(content=response).send()
