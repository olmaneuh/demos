from pydantic import BaseModel, Field


class SQLQueryOutputSchema(BaseModel):
    """Generated SQL query."""

    sql_query: str = Field(
        ...,
        description="Syntactically valid SQL query.",
        examples=["SELECT COUNT(id) AS total_customers FROM customers;"],
    )
