import os
import streamlit as st

from database import db
from dotenv import load_dotenv
from langchain import hub
from langchain_core.prompt_values import ChatPromptValue
from langchain_ibm import ChatWatsonx
from schemas import SQLQueryOutputSchema
from typing import Any, Dict


BASE_URL = "https://us-south.ml.cloud.ibm.com"
MODEL_ID = "ibm/granite-3-2b-instruct"


def load_credentials() -> Dict[str, str]:
    """Loads credentials from environment variables."""

    load_dotenv()

    watsonx_project_id = os.getenv("WATSONX_PROJECT_ID")
    apikey = os.getenv("API_KEY")

    if not watsonx_project_id or not apikey:
        raise ValueError("Missing credentials. Check your environment variables.")

    return {"project_id": watsonx_project_id, "apikey": apikey}


def init_state() -> None:
    """Initializes the session state if not already set."""

    if "sql_query" not in st.session_state:
        st.session_state["sql_query"] = ""


@st.cache_resource(show_spinner="Loading the model...")
def get_model(credentials: Dict[str, str]) -> ChatWatsonx:
    """Instantiates and returns a watsonx hosted model using provided credentials."""

    return ChatWatsonx(
        model_id=MODEL_ID,
        url=BASE_URL,
        project_id=credentials.get("project_id"),
        apikey=credentials.get("apikey"),
    )


def get_query_prompt_value(prompt_input: Dict[str, Any]) -> ChatPromptValue:
    """Generates a chat prompt based on the input and a community prompt template."""

    query_prompt_template = hub.pull("langchain-ai/sql-query-system-prompt")

    return query_prompt_template.invoke(prompt_input)


def generate_sql_query(model: ChatWatsonx, user_input: str) -> str:
    """Generates an SQL query based on the user input question using the provided model."""

    prompt_input = {
        "dialect": db.dialect,
        "top_k": 10,
        "table_info": db.get_table_info(),
        "input": user_input,
    }

    prompt = get_query_prompt_value(prompt_input)
    model_with_structure = model.with_structured_output(SQLQueryOutputSchema)
    structured_response = model_with_structure.invoke(prompt)

    return structured_response.sql_query


def main() -> None:
    """Main function to run the app."""

    try:
        # display app header
        st.title("From Natural Language To SQL With watsonx")

        # load credentials
        credentials = load_credentials()

        # init application state
        init_state()

        # load the model
        model = get_model(credentials)

        # create two columns for side-by-side layout
        col1, col2 = st.columns(2)

        # display left-side for user input
        with col1:
            user_input = st.text_area(label="Question", height=200)

        # display right-side for sql query generated
        with col2:
            st.text_area(
                label="SQL Query",
                value=st.session_state.get("sql_query"),
                height=200,
                disabled=True,
            )

        # generate sql query when the user clicks the button
        if st.button("Generate SQL Query"):

            if not user_input:
                st.error("Please enter a question to generate an SQL query.")
                return

            with st.spinner("Generating SQL query..."):
                st.session_state["sql_query"] = generate_sql_query(model, user_input)

            st.rerun()

    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
