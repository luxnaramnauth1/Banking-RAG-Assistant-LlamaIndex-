"""Banking assistant combining a RAG index over policy documents with a SQL
query engine over customer data, orchestrated by a ReAct agent.

Run:  streamlit run rag_app.py
Requires OPENAI_API_KEY in the environment.
"""
import os

import streamlit as st
from sqlalchemy import create_engine
from llama_index.core import (
    Settings,
    SimpleDirectoryReader,
    SQLDatabase,
    VectorStoreIndex,
)
from llama_index.core.agent import ReActAgent
from llama_index.core.query_engine import NLSQLTableQueryEngine
from llama_index.core.tools import QueryEngineTool
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

DOCS_DIR = "docs"
DB_URL = "sqlite:///bank.db"


@st.cache_resource(show_spinner="Loading policy documents...")
def build_policy_tool():
    Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0)
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
    documents = SimpleDirectoryReader(DOCS_DIR).load_data()
    index = VectorStoreIndex.from_documents(documents)
    return QueryEngineTool.from_defaults(
        query_engine=index.as_query_engine(similarity_top_k=3),
        name="policy_search",
        description=(
            "Answers questions about bank policies: account opening, fees, "
            "loans, card security and digital banking rules."
        ),
    )


@st.cache_resource(show_spinner="Connecting to customer database...")
def build_sql_tool():
    engine = create_engine(DB_URL)
    sql_database = SQLDatabase(engine, include_tables=["customers", "accounts", "transactions"])
    query_engine = NLSQLTableQueryEngine(
        sql_database=sql_database,
        tables=["customers", "accounts", "transactions"],
    )
    return QueryEngineTool.from_defaults(
        query_engine=query_engine,
        name="customer_data",
        description=(
            "Answers questions about customers, account balances and recent "
            "transactions from the bank database."
        ),
    )


@st.cache_resource
def build_agent():
    tools = [build_policy_tool(), build_sql_tool()]
    return ReActAgent.from_tools(
        tools,
        llm=Settings.llm,
        verbose=False,
        system_prompt=(
            "You are a banking assistant. Use policy_search for rules and fees, "
            "and customer_data for balances and transactions. Never reveal "
            "one-time passwords or full card numbers. Say so if you do not know."
        ),
    )


def main():
    st.set_page_config(page_title="Banking Assistant", page_icon="🏦")
    st.title("🏦 Banking Assistant")
    st.caption("Ask about bank policies, fees, loans, or customer account data.")

    if not os.getenv("OPENAI_API_KEY"):
        st.error("Set the OPENAI_API_KEY environment variable and restart the app.")
        return

    agent = build_agent()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("e.g. What is the overdraft fee? / What is Amit's savings balance?")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                answer = str(agent.chat(prompt))
            st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    main()
