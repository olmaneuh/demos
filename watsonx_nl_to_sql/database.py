from langchain_community.utilities import SQLDatabase


db = SQLDatabase.from_uri("sqlite:///./sales.db")
