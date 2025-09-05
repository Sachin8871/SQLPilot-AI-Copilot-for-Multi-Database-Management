from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain.callbacks.manager import tracing_v2_enabled
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
from pydantic import BaseModel, Field
from typing import TypedDict, Literal
from langgraph.types import Command
import streamlit as st
import os


def graph(user_input):
    st.session_state.user_input_fleg = False
    db_engine = st.session_state.db_engine
    model = st.session_state.model

    #========================================= State Section ===================================================

    class QueryState(TypedDict):
        messages: Annotated[list[BaseMessage], add_messages]
        task: Literal["Normal_question", "SQL_query"]
        query: str
        type: Literal["read", "modufy"]
        validation_status: Literal["correct", "wrong"]
        validation_feedback: str
        current_iteration: int
        max_iteration: int
        normal_input_ans: str
        query_result: str

    #========================================= Model Schema Section ===================================================

    class Input_Rewriter_Schema(BaseModel):
        task: Literal["Normal_question", "SQL_query"] = Field(discription="Return input's task.")
        updated_input: str = Field(discription=f"'Rewrite the user input so that an LLM can write a best answer for it' or 'write SQL query suggetion'.")

    class Query_Generater_Schema(BaseModel):
        query: str = Field(discription=f"Write a {db_engine} query for the user input.")
        type: Literal["read", "modify"] = Field(description="Determine whether the query is for read or modify.")

    class Validation_Schema(BaseModel):
        validation_status: Literal["correct", "wrong"] = Field(discription="Ditermine weather the query is correct or wrong.")
        validation_feedback: str = Field(discription="Wrong query feedback. If the query is correct, leave blank.")

    #=========================================== Model Section ========================================================

    input_rewriter_model = model.with_structured_output(Input_Rewriter_Schema)
    query_genarater_model = model.with_structured_output(Query_Generater_Schema)
    validation_model = model.with_structured_output(Validation_Schema)

    #========================================= Node/Function Section ===================================================

    def refined_input(state: QueryState):
        
        prompt = ChatPromptTemplate.from_messages([
            ("system",
            f"You are an assistant."
            "You are given an user input."
            f"Your first task is to determine weather the user input is normal real world question or want to ask/execute some SQL query for the following SQL database structure:\n {st.session_state.database_info_str}\n."
            f"Your second task is to rewite user input."
            "Return only the task and update user input. Do not try to solve it."
            ),
            MessagesPlaceholder(variable_name="user_input")
        ])

        chain = prompt | input_rewriter_model
        response = chain.invoke({"user_input": state["messages"]})

        if response.task == "Normal_question":
            return Command(
                update = {"messages": response.updated_input, "task":response.task},
                goto = "normal_question_ans"
            )
        else:
            return Command(
                update = {"messages": response.updated_input, "task":response.task},
                goto = "generate_query"
            )
        
    #----------------------------------- Normal Question Ans Node -----------------------------------

    def normal_question_ans(state:QueryState):
        messages = state["messages"]
        prompt = ChatPromptTemplate.from_messages([
            ("system",
            "You are given an question / user input."
            "Answer the following question as an conversetion between an user and assistant."
            "Answer in max 100 words."
            ),
            MessagesPlaceholder(variable_name="question")
        ])

        chain = prompt | model
        response = chain.invoke({"question":messages})
        st.session_state.state = state
        return Command(
            update = {"normal_input_ans": response.content, "messages": [AIMessage(content=response.content)]},
            goto = END
        )

    #----------------------------------- Generate query Node -----------------------------------

    def generate_query(state: QueryState):
        messages = state["messages"]
        prompt = ChatPromptTemplate.from_messages([
            ("system",
            f"You are an assistant. The user is working with {db_engine}.\n\n"
            f"The database contains the following structure:\n{st.session_state.database_info_str}\n\n"
            f"Your job is to generate a valid SQL query specifically for {db_engine}.\n"
            "⚠️ Return only the SQL query in plain text (no explanations or formatting like ```sql).\n\n"
            "🧠 Rules:\n"
            f"- If the query is unsupported in {db_engine} then explain problem and suggest an alternative that works (In max 5 lines).\n"
            "- If no tables exist, say so.\n"
            f"- If the query is not possible for {db_engine}, then say 'Not Possible'.\n"
            ),
            MessagesPlaceholder(variable_name="messages")
        ])

        chain = prompt | query_genarater_model
        response = chain.invoke({"messages": messages})

        return Command(
            update = {"query": response.query, "type": response.type},
            goto = "query_validation"
        )

    #------------------------------------ Query validation Node ------------------------------------

    def query_validation(state: QueryState):
        prompt = ChatPromptTemplate.from_messages([
            ("system",
            f"You are a SQL assistant. "
            f"Your first task is to check whether the query is for {db_engine} or not. "
            f"If it is not for {db_engine}, return wrong and write the feedback accordingly. "
            f"Your second task is to check whether the given query is correct or not for the user input and database structure {st.session_state.database_info_str}. "
            f"If it is correct, return as it is. "
            f"If it is wrong, give a feedback."
            ),
            MessagesPlaceholder(variable_name="User input"),
            MessagesPlaceholder(variable_name="query")
        ])

        chain = prompt | validation_model
        response = chain.invoke({
            # "User input": [HumanMessage(content=state["user_input"])],
            "User input": [user_input],
            "query": [HumanMessage(content=state["query"])]
        })

        if response.validation_status == "wrong" and (state["max_iteration"] > state["current_iteration"]):
            return Command(
                update = {"validation_status": response.validation_status,"validation_feedback": response.validation_feedback},
                goto = "update_query"
            )
        else:
            return Command(
                update = {"validation_status": response.validation_status,"validation_feedback": response.validation_feedback, "messages":[AIMessage(content=state['query'])]},
                goto = END
            )

    #-------------------------------------- Query updation Node -------------------------------------

    def query_updation(state: QueryState):
        prompt = ChatPromptTemplate.from_messages([
            ("system",
            f"You are an SQL assistant. The user is working with {db_engine}.\n\n"
            f"The database contains the following structure:\n{st.session_state.database_info_str}\n\n"
            f"Your job is to correct or update the following query according to the feedback.\n"
            f"Also check whether the query is for read only or for modification."
            ),
            MessagesPlaceholder(variable_name="messages"),
            MessagesPlaceholder(variable_name="feedback")
        ])

        chain = prompt | query_genarater_model
        response = chain.invoke({
            "messages": [HumanMessage(content=state["query"])],
            "feedback": [HumanMessage(content=state["validation_feedback"])]
        })

        iteration = state["current_iteration"] + 1

        return Command(
            update = {"query": response.query, "type": response.type, "current_iteration": iteration},
            goto = "query_validation"
        )

    #========================================= Graph Nodes Section ===================================================

    builder = StateGraph(QueryState)

    builder.add_node("refine_input", refined_input)
    builder.add_node("normal_question_ans", normal_question_ans)
    builder.add_node("generate_query", generate_query)
    builder.add_node("query_validation", query_validation)
    builder.add_node("update_query", query_updation)

    #========================================= Graph compile Section ===================================================


    if "checkpointer" not in st.session_state:
        st.session_state.checkpointer = InMemorySaver()

    builder.set_entry_point("refine_input")
    graph = builder.compile(checkpointer=st.session_state.checkpointer)

    initial_state = {
        # "user_input": [HumanMessage(content=user_input)],
        "messages": [HumanMessage(content=user_input)],
        "max_iteration": 3,
        "current_iteration": 0
    }

    with tracing_v2_enabled(project_name=os.getenv("LANGCHAIN_PROJECT", "SQL")):
        response = graph.invoke(initial_state, config=st.session_state.config)
        st.session_state.state = response

    return st.session_state.state

