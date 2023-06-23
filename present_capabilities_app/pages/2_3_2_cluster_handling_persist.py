import streamlit as st
import json

st.set_page_config(
    page_title="Brand cluster date handling tool", page_icon="📊", layout="wide"
)

file = "../clusters/similar-brand-clusters.json"
with open(file=file) as f:
    brand_clusters = json.load(f)
    if "-1" in brand_clusters:
        del brand_clusters["-1"]

actions_file = "./pages/data_files/brand_cluster_actions.json"
with open(file=actions_file, mode="r") as a:
    try:
        actions_from_file = json.load(a)
        print(f"actions_from_file:{actions_from_file}")
        st.session_state["actions"] = actions_from_file

    except:
        st.session_state["actions"] = {}
