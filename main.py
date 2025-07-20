import os
import requests
import streamlit as st
from typing import Dict, Any, Optional, List
import json
from dotenv import load_dotenv

# Загружает переменные из .env в окружение
load_dotenv()

# Constants
LANGFLOW_API_URL = "http://localhost:7860/api/v1/run/c804dda5-f459-472d-a364-f83e4d7cb1e8"
SESSION_CHATS_KEY = "chat_sessions"
CURRENT_CHAT_KEY = "current_chat"
PROMPT_TEMPLATES = {
    "технический специалист": "Привет! Я - технический специалист с глубокими знаниями в IT. Чем тебе помочь сегодня?",
    "менеджер": "Привет! Я - опытный менеджер. Отвечаю вежливо, структурированно, с акцентом на бизнес-выгоду. Чем тебе помочь сегодня?",
    "стандарт": "Привет! Я твой ассистент. Чем тебе помочь сегодня?"
}

class LangflowAgent:
    """Wrapper class for Langflow API interactions."""
    
    def __init__(self):
        self.api_url = LANGFLOW_API_URL
        self.api_key = self._get_api_key()
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key
        }
    
    def _get_api_key(self) -> str:
        """Retrieve API key from environment variables."""
        try:
            return os.environ["LANGFLOW_API_KEY"]
        except KeyError:
            raise ValueError(
                "LANGFLOW_API_KEY environment variable not found. "
                "Please set your API key in the environment variables."
            )
    
    def query_agent(self, user_input: str) -> Optional[str]:
        """Send query to Langflow agent and return parsed text response."""
        payload = {
            "output_type": "chat",
            "input_type": "chat",
            "input_value": user_input
        }
        
        try:
            response = requests.post(
                self.api_url,
                json=payload,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            response_data = response.json()
            return response_data['outputs'][0]['outputs'][0]['results']['message']['data']['text']
            
        except requests.exceptions.RequestException as e:
            st.error(f"Error making API request: {e}")
            return None
        except json.JSONDecodeError:
            st.error("Failed to parse API response as JSON")
            return None

def initialize_session_state():
    """Initialize session state for message history and chat sessions."""
    if SESSION_CHATS_KEY not in st.session_state:
        st.session_state[SESSION_CHATS_KEY] = {}
        
    if CURRENT_CHAT_KEY not in st.session_state or not st.session_state[SESSION_CHATS_KEY]:
        # Create first chat if none exists
        create_new_chat("стандарт")

def display_chat_messages():
    """Display chat messages from current chat session."""
    current_chat_id = st.session_state[CURRENT_CHAT_KEY]
    messages = st.session_state[SESSION_CHATS_KEY].get(current_chat_id, {}).get("messages", [])
    
    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def handle_user_input(agent: LangflowAgent):
    """Handle user input and generate AI response."""
    if user_input := st.chat_input("Type your message here..."):
        current_chat_id = st.session_state[CURRENT_CHAT_KEY]
        
        # Add user message to current chat history
        st.session_state[SESSION_CHATS_KEY][current_chat_id]["messages"].append(
            {"role": "user", "content": user_input}
        )
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Generate AI response
        with st.spinner("Thinking..."):
            ai_response = agent.query_agent(user_input)
        
        if ai_response is not None:
            # Add AI response to current chat history and display it
            st.session_state[SESSION_CHATS_KEY][current_chat_id]["messages"].append(
                {"role": "assistant", "content": ai_response}
            )
            with st.chat_message("assistant"):
                st.markdown(ai_response)

def create_new_chat(prompt_type: str):
    """Create a new chat session with specified prompt type."""
    new_chat_id = len(st.session_state[SESSION_CHATS_KEY]) + 1
    st.session_state[CURRENT_CHAT_KEY] = new_chat_id
    st.session_state[SESSION_CHATS_KEY][new_chat_id] = {
        "title": prompt_type,
        "prompt_type": prompt_type,
        "messages": [
            {"role": "assistant", "content": PROMPT_TEMPLATES[prompt_type]}
        ]
    }
    #st.rerun()

def delete_chat(chat_id: int):
    """Delete a chat session."""
    if chat_id in st.session_state[SESSION_CHATS_KEY]:
        del st.session_state[SESSION_CHATS_KEY][chat_id]
        
        # If we deleted the current chat, switch to another one
        if st.session_state[CURRENT_CHAT_KEY] == chat_id:
            if st.session_state[SESSION_CHATS_KEY]:
                st.session_state[CURRENT_CHAT_KEY] = max(st.session_state[SESSION_CHATS_KEY].keys())
            else:
                create_new_chat("стандарт")
        #st.rerun()

def display_prompt_selector():
    """Display prompt selection dropdown."""
    with st.sidebar:
        if st.button("Новый чат", use_container_width=True):
            st.session_state["show_prompts"] = not st.session_state.get("show_prompts", False)
        
        if st.session_state.get("show_prompts", False):
            st.write("Выберите тип чата:")
            cols = st.columns(3)
            with cols[0]:
                if st.button("Технический", help="Технический специалист"):
                    create_new_chat("технический специалист")
            with cols[1]:
                if st.button("Менеджер", help="Бизнес-менеджер"):
                    create_new_chat("менеджер")
            with cols[2]:
                if st.button("Стандарт", help="Стандартный ассистент"):
                    create_new_chat("стандарт")

def display_chat_sidebar():
    """Display sidebar with chat history and controls."""
    with st.sidebar:
        st.header("История чатов")
        
        # New chat and prompt buttons
        cols = st.columns(2)
        with cols[1]:
            display_prompt_selector()
        
        # Display list of existing chats
        st.subheader("Ваши чаты")
        for chat_id, chat_data in sorted(
            st.session_state[SESSION_CHATS_KEY].items(),
            key=lambda x: x[0],
            reverse=True
        ):
            title = chat_data["title"]
            msg_count = len(chat_data["messages"])
            
            # Create container for each chat with buttons
            chat_container = st.container()
            with chat_container:
                cols = st.columns([4, 1])
                with cols[0]:
                    if st.button(
                        f"{title} ({msg_count} сообщ.)",
                        key=f"chat_btn_{chat_id}",
                        use_container_width=True,
                        type="primary" if chat_id == st.session_state[CURRENT_CHAT_KEY] else "secondary"
                    ):
                        st.session_state[CURRENT_CHAT_KEY] = chat_id
                        st.rerun()
                with cols[1]:
                    if st.button(
                        "🗑️",
                        key=f"delete_btn_{chat_id}",
                        help="Удалить чат",
                        on_click=lambda cid=chat_id: delete_chat(cid)
                    ):
                        pass

def configure_page():
    """Configure Streamlit page settings."""
    st.set_page_config(
        page_title="AI Chat Assistant",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    st.title("AI Chat Assistant")

def main():
    """Main application function."""
    configure_page()
    initialize_session_state()
    
    # Display sidebar with chat history
    display_chat_sidebar()
    
    # Main chat area
    with st.container():
        try:
            agent = LangflowAgent()
            display_chat_messages()
            handle_user_input(agent)
        except ValueError as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    main()