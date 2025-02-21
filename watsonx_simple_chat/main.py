import os
import streamlit as st

from dotenv import load_dotenv
from ibm_watson_machine_learning.foundation_models import ModelInference
from typing import Dict, Optional, Generator


BASE_URL = 'https://us-south.ml.cloud.ibm.com'
MODEL_ID = 'ibm/granite-3-8b-instruct'
MODEL_PARAMETERS = {
    'decoding_method': 'greedy',
    'max_new_tokens': 100,
    'min_new_tokens': 0,
    'repetition_penalty': 1,
    'stop_sequences': ['.']
}


def load_api_credentials() -> Dict[str, Optional[str]]:
    """load api credentials from env variables."""

    load_dotenv()

    return {
        'project_id': os.getenv('WATSONX_PROJECT_ID'),
        'apikey': os.getenv('API_KEY')
    }


@st.cache_resource(show_spinner='Loading LLM...')
def get_model(credentials: Dict[str, Optional[str]]) -> ModelInference:
    """instantiate and return a watsonx hosted llm object."""

    try:
        if not credentials['apikey'] or not credentials['project_id']:
            st.error('Missing API credentials. Check your environment variables.')
            return

        return ModelInference(
            model_id=MODEL_ID,
            params=MODEL_PARAMETERS,
            credentials={'url': BASE_URL, 'apikey': credentials['apikey']},
            project_id=credentials['project_id']
        )
    except Exception as e:
        st.error(f'Error loading model: {e}')


def build_prompt(user_input: str) -> str:
    """constructs the final prompt to send to the llm."""

    # prompt used to tune the llm as an assistant
    system_prompt = (
        '<|start_of_role|>system<|end_of_role|>You are Granite, an AI language model developed by IBM in 2024. '
        'You are a cautious assistant. You carefully follow instructions. '
        'You are helpful and harmless and you follow ethical guidelines and promote positive behavior.<|end_of_text|>\n'
    )

    # include all the chat messages for context reference
    messages_prompt = ''.join(
        f'<|start_of_role|>{message["role"]}<|end_of_role|>{message["content"]}<|end_of_text|>\n'
        for message in st.session_state.messages
    )

    # adding the last input from the user and return the final prompt
    return f'{system_prompt}{messages_prompt}<|start_of_role|>user<|end_of_role|>{user_input}<|end_of_text|>\n<|start_of_role|>assistant<|end_of_role|>\n'


def generate_response(model: ModelInference, user_input: str) -> Generator[str, None, None]:
    """generates a response from the llm."""

    try:
        prompt = build_prompt(user_input)
        return model.generate_text_stream(prompt=prompt, guardrails=True)
    except Exception as e:
        st.error(f'Error generating a response: {e}')
        return iter(['Error generating a response. Please try again.'])


def main() -> None:
    """main function to run the app."""

    # display app header
    st.title('Chat With watsonx')
    st.write(f'**Model:** {MODEL_ID}')
    st.divider()

    # init chat history
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    # load credentials and model
    credentials = load_api_credentials()
    model = get_model(credentials)

    # display chat messages from the history
    for message in st.session_state.messages:
        with st.chat_message(message['role']):
            st.write(message['content'])

    # read and display user input
    if user_input := st.chat_input('Tell me something...'):
        with st.chat_message('user'):
            st.write(user_input)

        # add user input to chat history
        st.session_state.messages.append(
            {'role': 'user', 'content': user_input}
        )

        # generate and display llm response
        with st.chat_message('assistant'):
            llm_response = st.write_stream(
                generate_response(model, user_input)
            )

        # add llm response to the chat history
        if llm_response:
            st.session_state.messages.append(
                {'role': 'assistant', 'content': llm_response}
            )


if __name__ == '__main__':
    main()
