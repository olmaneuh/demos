import os
import streamlit as st

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_ibm import ChatWatsonx
from typing import Dict, Iterator


BASE_URL = "https://us-south.ml.cloud.ibm.com"
MODEL_ID = "ibm/granite-3-8b-instruct"
MODEL_PARAMETERS = {
    "decoding_method": "greedy",
    "max_new_tokens": 100,
    "min_new_tokens": 0,
    "repetition_penalty": 1,
    "stop_sequences": ["."],
}


def get_system_message() -> SystemMessage:
    """Returns the initial system message for the AI model."""

    return SystemMessage(
        content=(
            "You are Granite, an AI language model developed by IBM in 2024. "
            "You are a cautious assistant. You carefully follow instructions. "
            "You are helpful and harmless and you follow ethical guidelines and promote positive behavior."
        )
    )


def load_api_credentials() -> Dict[str, str]:
    """Loads API credentials from environment variables."""

    load_dotenv()

    return {
        "project_id": os.getenv("WATSONX_PROJECT_ID"),
        "apikey": os.getenv("API_KEY"),
    }


@st.cache_resource(show_spinner="Loading the model...")
def init_model(credentials: Dict[str, str]) -> ChatWatsonx:
    """Instantiates and returns a watsonx hosted model."""

    project_id, apikey = credentials.get("project_id"), credentials.get("apikey")

    if not project_id or not apikey:
        st.error("Missing API credentials. Check your environment variables.")
        return

    try:
        return ChatWatsonx(
            model_id=MODEL_ID,
            params=MODEL_PARAMETERS,
            url=BASE_URL,
            project_id=project_id,
            apikey=apikey,
        )
    except Exception as e:
        st.error(f"Error initializing the model: {e}")


def generate_response(model: ChatWatsonx, chat_history: list) -> Iterator:
    """Generates a response from the LLM."""

    if not model:
        yield "Error: Model is not initialized."
        return

    try:
        yield from model.stream(input=chat_history)
    except Exception as e:
        st.error(f"Error generating a response: {e}")
        yield "Error: Error generating a response. Please try again."


def display_messages():
    """Displays all chat messages."""

    for message in st.session_state.messages:
        match message:
            case HumanMessage():
                role = "user"
            case AIMessage():
                role = "assistant"
            case _:
                continue

        with st.chat_message(role):
            st.write(message.content)


def main() -> None:
    """Main function to run the app."""

    # display app header
    st.title("Chat With LangChain & watsonx")
    st.write(f"**Model:** {MODEL_ID}")
    st.divider()

    # init chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [get_system_message()]

    # load credentials
    credentials = load_api_credentials()

    # init the model
    model = init_model(credentials)

    # display chat history
    display_messages()

    # process user input
    if user_input := st.chat_input("Tell me something..."):

        # display user input
        with st.chat_message("user"):
            st.write(user_input)

        # add user input to chat history
        st.session_state.messages.append(HumanMessage(content=user_input))

        # generate and display a model response
        with st.chat_message("assistant"):
            response = st.write_stream(
                generate_response(model, st.session_state.messages)
            )

        # add response to the chat history
        if response:
            st.session_state.messages.append(AIMessage(content=response))


if __name__ == "__main__":
    main()
