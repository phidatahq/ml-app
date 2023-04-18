import streamlit as st

st.set_page_config(
    page_title="ML Apps",
    page_icon="🚝",
)

st.markdown("### Select a Demo from the sidebar:")
st.markdown("1. TimeSeries Forecast: Predict stock price using Prophet")
st.markdown("2. Plotting Demo: Plot random numbers")
st.markdown("\n")

st.sidebar.success("Select a Demo from above")
