import streamlit as st

st.title("IVO Electronics - SYSTEM TEST")
st.write("If you can see this, the system is WORKING.")

if st.button("CLICK TO START SHOP"):
    st.balloons()
    st.success("System Connection Stable!")
