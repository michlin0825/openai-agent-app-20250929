import chainlit as cl
import os
from dotenv import load_dotenv
from agent import OpenAIAgent

load_dotenv()

# Initialize agent
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
    await cl.Message(content="Hello! I'm your AI assistant with access to documents and web search. I can help you with questions about Amazon's 2023 shareholder letter or current information. How can I assist you today?").send()

@cl.on_message
async def main(message: cl.Message):
    session_id = cl.user_session.get("session_id", "default")
    response = agent.process_query(message.content, session_id)
    await cl.Message(content=response).send()
