from langchain_community.utilities import SQLDatabase

# instance of SQLDatabase connected to the database using the provided URI.
db = SQLDatabase.from_uri("sqlite:///./sales.db")
