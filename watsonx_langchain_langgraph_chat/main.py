import os
import streamlit as st

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.prompt_values import ChatPromptValue
from langchain_ibm import ChatWatsonx
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import MessagesState, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from typing import Dict, Iterator, List


# credentials
# these values will be updated to use the environment variables value
watsonx_project_id = ""
api_key = ""

BASE_URL = "https://us-south.ml.cloud.ibm.com"
MODEL_ID = "ibm/granite-3-8b-instruct"
MODEL_PARAMETERS = {
    "temperature": 1,
    "max_tokens": 100,
    "frequency_penalty": 1,
    "stop": ["."],
}
CONFIG = {"configurable": {"thread_id": "1234"}}


def load_credentials() -> None:
    """Loads API credentials from environment variables."""

    load_dotenv()

    globals()["watsonx_project_id"] = os.getenv("WATSONX_PROJECT_ID")
    globals()["api_key"] = os.getenv("API_KEY")

    if not watsonx_project_id or not api_key:
        raise ValueError("Missing credentials. Check your environment variables.")


def get_chat_prompt_value(state: MessagesState) -> ChatPromptValue:
    """Generates a chat prompt based on the conversation history."""

    system_message_content = (
        "You are Granite, an AI language model developed by IBM in 2024. "
        "You are a cautious assistant. You carefully follow instructions. "
        "You are helpful and harmless and you follow ethical guidelines and promote positive behavior."
    )

    prompt_template = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=system_message_content),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    return prompt_template.invoke(state)


@st.cache_resource(show_spinner="Loading the model...")
def get_model() -> ChatWatsonx:
    """Instantiates and returns a watsonx hosted model."""

    return ChatWatsonx(
        model_id=MODEL_ID,
        params=MODEL_PARAMETERS,
        url=BASE_URL,
        project_id=watsonx_project_id,
        apikey=api_key,
    )


def generate_response(state: MessagesState) -> Dict[str, AIMessage]:
    """Generates a response from the model based on the conversation state."""

    try:
        prompt = get_chat_prompt_value(state)
        model = get_model()

        response = model.invoke(prompt)

        return {"messages": response}
    except Exception as e:
        error_message = AIMessage(
            content="Error: There was an error generating a response. Please try again later."
        )
        return {"messages": error_message}


@st.cache_resource(show_spinner="Initializing the application graph...")
def init_graph() -> CompiledStateGraph:
    """Initializes and compiles the application graph."""

    graph_builder = StateGraph(state_schema=MessagesState)

    graph_builder.add_edge(start_key=START, end_key="generate_response")
    graph_builder.add_node(node="generate_response", action=generate_response)

    return graph_builder.compile(checkpointer=MemorySaver())


def display_chat_history(chat_history: List[BaseMessage]) -> None:
    """Displays the chat history in the UI."""

    for message in chat_history:
        role = "assistant" if isinstance(message, AIMessage) else "user"
        with st.chat_message(role):
            st.write(message.content)


def get_response(graph: CompiledStateGraph, user_input: str) -> Iterator:
    """Streams the response from the model."""

    for chunk, _ in graph.stream(
        {"messages": HumanMessage(user_input)}, CONFIG, stream_mode="messages"
    ):
        yield chunk.content


def main() -> None:
    """Main function to run the app."""
    try:
        # display app header
        st.title("Chat With LangChain, LangGraph & watsonx")
        st.write(f"**Model:** {MODEL_ID}")
        st.divider()

        # load credentials
        load_credentials()

        # pre-cache the model
        _ = get_model()

        # init the application graph
        graph = init_graph()

        # display chat history
        chat_history = graph.get_state(CONFIG).values.get("messages", [])
        display_chat_history(chat_history)

        # process user input
        if user_input := st.chat_input("Tell me something..."):

            # display user input
            with st.chat_message("user"):
                st.write(user_input)

            # generate and display a model response
            with st.chat_message("assistant"):
                st.write_stream(get_response(graph, user_input))

    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
