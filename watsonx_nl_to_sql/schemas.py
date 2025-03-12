from pydantic import BaseModel, Field


class SQLQueryOutputSchema(BaseModel):
    """TODO"""

    sql_query: str = Field(description="Syntactically valid SQL query.")
