from os import getenv, environ
from typing import Optional

import streamlit as st
from duckdb import DuckDBPyConnection
from streamlit_chat import message

from phidata.llm.duckdb.agent import create_duckdb_agent
from phidata.llm.duckdb.connection import create_duckdb_connection
from phidata.llm.duckdb.loader import load_s3_path_to_table
from phidata.llm.duckdb.query import run_duckdb_query


# -*- List of test datasets
Tables = {
    "Titanic": "s3://phidata-public/demo_data/titanic.csv",
    "Census": "s3://phidata-public/demo_data/census_2017.csv",
    "Covid": "s3://phidata-public/demo_data/covid_19_data.csv",
    "Air Quality": "s3://phidata-public/demo_data/air_quality.csv",
}


#
# -*- Sidebar component to get OpenAI API key
#
def get_openai_key() -> Optional[str]:
    # Get OpenAI API key from environment variable
    OPENAI_API_KEY: Optional[str] = getenv("OPENAI_API_KEY")
    # If not found, get it from user input
    if OPENAI_API_KEY is None or OPENAI_API_KEY == "" or OPENAI_API_KEY == "sk-***":
        api_key = st.sidebar.text_input("OpenAI API key", value="sk-***", key="api_key")
        if api_key != "sk-***":
            OPENAI_API_KEY = api_key
            st.session_state["OPENAI_API_KEY"] = OPENAI_API_KEY
            environ["OPENAI_API_KEY"] = OPENAI_API_KEY

    # Store it in session state and environment variable
    if OPENAI_API_KEY is not None:
        st.session_state["OPENAI_API_KEY"] = OPENAI_API_KEY
        environ["OPENAI_API_KEY"] = OPENAI_API_KEY

    return OPENAI_API_KEY


#
# -*- Sidebar component to get S3 data path
#
def get_input_data_path() -> None:
    # Get the data source
    input_data_source = st.sidebar.radio(
        "Select Data Source", options=["Table", "S3 Path"]
    )
    if "input_data_source" not in st.session_state:
        if input_data_source is not None:
            st.session_state["input_data_source"] = input_data_source

    s3_data_path = None
    if input_data_source == "Table":
        selected_table = st.sidebar.selectbox("Select Table", Tables.keys())
        if selected_table in Tables:
            s3_data_path = Tables[selected_table]
    elif input_data_source == "S3 Path":
        selected_s3_path = st.sidebar.text_input(
            "S3 Path", value="s3://bucket-name/path/to/file"
        )
        s3_data_path = selected_s3_path

    # Store it in session state
    if "s3_data_path" not in st.session_state:
        if s3_data_path is not None:
            st.session_state["s3_data_path"] = s3_data_path


#
# -*- Sidebar component to read data and return the duckdb connection
#
def read_data():
    # Get duckdb connection
    duckdb_conn: Optional[DuckDBPyConnection] = st.session_state.get(
        "duckdb_connection", None
    )
    if st.sidebar.button("Read Data"):
        # Create duckdb connection if not available
        if duckdb_conn is None:
            duckdb_conn = create_duckdb_connection()

        s3_data_path = st.session_state.get("s3_data_path", None)
        if duckdb_conn is not None:
            st.session_state["duckdb_connection"] = duckdb_conn
            if s3_data_path is not None:
                table_name, executed_query = load_s3_path_to_table(
                    duckdb_conn, s3_data_path
                )
                st.session_state["table_name"] = table_name
                st.session_state["executed_queries"] = [executed_query]
                st.session_state["data_loaded"] = True


#
# -*- Sidebar component to show status
#
def show_status():
    st.sidebar.markdown("## Status")
    if "OPENAI_API_KEY" in st.session_state:
        st.sidebar.markdown("🔑  OpenAI API key set")
    if "duckdb_connection" in st.session_state:
        st.sidebar.markdown("📡  Duckdb connection created")
    if "data_loaded" in st.session_state:
        st.sidebar.markdown("🦆  Data loaded to duckdb")
    if "agent" in st.session_state:
        st.sidebar.markdown("🤖  Agent created")
    if "QueryStatus" in st.session_state:
        st.sidebar.markdown("QueryStatus: " + st.session_state["QueryStatus"])


#
# -*- Create duckdb agent
#
def create_agent() -> None:
    # Get duckdb connection
    duckdb_connection = st.session_state.get("duckdb_connection", None)
    if duckdb_connection is not None:
        # Create an OpenAI agent if not already created
        agent = st.session_state.get("agent", None)
        if agent is None:
            agent = create_duckdb_agent(duckdb_connection=duckdb_connection)
            st.session_state["agent"] = agent


#
# -*- Sidebar component to show reload button
#
def show_reload():
    st.sidebar.markdown("---")
    if st.sidebar.button("Reload Session"):
        st.session_state.clear()
        st.experimental_rerun()


#
# -*- DuckGpt Sidebar
#
def duckgpt_sidebar():
    st.sidebar.markdown("# DuckGpt")

    # Get OpenAI API key
    openai_key = get_openai_key()
    if openai_key is None:
        st.write("🔑  OpenAI API key not set")

    # Choose data source
    get_input_data_path()

    # Read data
    read_data()

    # Create duckdb agent
    create_agent()

    # Show status on sidebar
    show_status()

    # Show reload button
    show_reload()


#
# -*- DuckGpt Main UI
#
def duckgpt_main():
    # Get duckdb connection
    duckdb_connection = st.session_state.get("duckdb_connection", None)
    if duckdb_connection is None:
        st.write("📡  Waiting for input")
        return

    # Get duckdb agent
    duckdb_agent = st.session_state.get("agent", None)
    if duckdb_agent is None:
        st.write("🤖  Waiting for Agent")
        return

    # User query input
    user_query = st.text_input(
        "Send a message:",
        placeholder="Describe this table",
        key="user_query",
    )
    st.session_state["QueryStatus"] = "Started"

    if user_query:
        # Create a session variable to store the chat
        if "chat_history" not in st.session_state:
            st.session_state["chat_history"] = [
                {
                    "role": "system",
                    "content": """You are a helpful assistant that answers natural language questions by querying data using duckdb""",  # noqa: E501
                },
            ]

        # Store the startup queries
        executed_queries = st.session_state.get("executed_queries", [])
        if len(executed_queries) > 0 and len(st.session_state["chat_history"]) == 1:
            st.session_state["chat_history"].append(
                {
                    "role": "system",
                    "content": """\b
                    Startup SQL Queries:
                    ```
                    {}
                    ```
                """.format(
                        "\n".join(executed_queries)
                    ),
                },
            )

        new_message = {"role": "user", "content": user_query}
        st.session_state["chat_history"].append(new_message)

        inputs = {
            "input": st.session_state["chat_history"],
            "table_names": run_duckdb_query(duckdb_connection, "show tables"),
        }

        # Generate response
        result = duckdb_agent(inputs)
        st.session_state["QueryStatus"] = "Processing"
        # st.write(result)

        # Store the output
        if "output" in result:
            st.session_state["chat_history"].append(
                {"role": "assistant", "content": result["output"]}
            )
        else:
            st.session_state["chat_history"].append(
                {
                    "role": "assistant",
                    "content": "Could not understand, please try again",
                }
            )
        st.session_state["QueryStatus"] = "Complete"

    if "chat_history" in st.session_state:
        for i in range(len(st.session_state["chat_history"]) - 1, -1, -1):
            msg = st.session_state["chat_history"][i]
            if msg["role"] == "user":
                message(msg["content"], is_user=True, key=str(i))
            elif msg["role"] == "assistant":
                message(msg["content"], key=str(i))
            elif msg["role"] == "system":
                message(msg["content"], key=str(i), seed=42)


#
# -*- DuckGpt UI
#
st.markdown("## DuckGpt")
st.write(
    """DuckGpt uses OpenAI, DuckDb and Langchain to interact with tables stored on s3.\n
    Read a table, send a message and it will respond.
    """
)

duckgpt_sidebar()
duckgpt_main()
