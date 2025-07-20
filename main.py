import os
import requests
import streamlit as st
from typing import Dict, Any, Optional
import json

from dotenv import load_dotenv

# Загружает переменные из .env в окружение
load_dotenv()

# Constants
LANGFLOW_API_URL = "http://localhost:7860/api/v1/run/c804dda5-f459-472d-a364-f83e4d7cb1e8"
SESSION_MESSAGES_KEY = "messages"
DEFAULT_WELCOME_MESSAGE = "Hello! I'm your AI assistant. How can I help you today?"


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
                timeout=10  # Add timeout to prevent hanging
            )
            response.raise_for_status()
            
            # Parse JSON response and extract text
            response_data = response.json()
            return self._extract_response_text(response_data)
            
        except requests.exceptions.RequestException as e:
            st.error(f"Error making API request: {e}")
            return None
        except json.JSONDecodeError:
            st.error("Failed to parse API response as JSON")
            return None
    
    def _extract_response_text(self, response_data: Dict[str, Any]) -> str:
        """Extract text response from API JSON data."""
        # Adjust this logic based on your actual API response structure
        if isinstance(response_data, dict):
            # Try common response formats
            if "text" in response_data:
                return response_data["text"]
            elif "response" in response_data:
                return response_data["response"]
            elif "result" in response_data:
                return response_data["result"]
            elif "output" in response_data:
                return response_data["output"]
        
        # Fallback: return the whole response as string if structure is unknown
        return str(response_data)


def initialize_session_state():
    """Initialize session state for message history."""
    if SESSION_MESSAGES_KEY not in st.session_state:
        st.session_state[SESSION_MESSAGES_KEY] = [
            {"role": "assistant", "content": DEFAULT_WELCOME_MESSAGE}
        ]


def display_chat_messages():
    """Display chat messages from session state."""
    for message in st.session_state[SESSION_MESSAGES_KEY]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def handle_user_input(agent: LangflowAgent):
    """Handle user input and generate AI response."""
    if user_input := st.chat_input("Type your message here..."):
        # Add user message to chat history
        st.session_state[SESSION_MESSAGES_KEY].append(
            {"role": "user", "content": user_input}
        )
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Generate AI response
        with st.spinner("Thinking..."):
            ai_response = agent.query_agent(user_input)
        
        # Only proceed if we got a valid response
        if ai_response is not None:
            # Add AI response to chat history and display it
            st.session_state[SESSION_MESSAGES_KEY].append(
                {"role": "assistant", "content": ai_response}
            )
            with st.chat_message("assistant"):
                st.markdown(ai_response)


def configure_page():
    """Configure Streamlit page settings."""
    st.set_page_config(
        page_title="AI Chat Assistant",
        page_icon="🤖",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    st.title("AI Chat Assistant")


def main():
    """Main application function."""
    configure_page()
    initialize_session_state()
    
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