import streamlit as st

st.set_page_config(
    page_title="ML Apps",
    page_icon="🚝",
)

st.markdown("### Select an App from the sidebar:")
st.markdown("1. Stock Prediction: Predict stock price using time series forecasting")
st.markdown("2. DuckGpt: Let GPT query your data using DuckDB")
st.markdown("\n")
st.markdown(
    "- built with [Streamlit](https://streamlit.io), [OpenAI](https://openai.com), [Langchain](https://langchain.readthedocs.io/en/latest/), [DuckDB](https://duckdb.org/) and [Phidata](https://docs.phidata.com)"  # noqa: E501
)

st.sidebar.success("Select an App from above")
