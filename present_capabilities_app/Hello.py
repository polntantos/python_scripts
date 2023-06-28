import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from classes.VirtuosoWrapper import VirtuosoWrapper

st.set_page_config(
    page_title="Hello",
    page_icon="👋",
)


import streamlit as st

query = """
select * 
where {
{
select distinct ?class ?p count(?o) as ?objectCount
  where {
    ?s a ?class.
    ?s ?p ?o.
  } group by ?class ?p
  order by ?class
} UNION { 
  select ?class COUNT(?s) as ?subjectCount 
  where{
    ?s a ?class.
  } group by ?class
}
}
"""
virtuoso = VirtuosoWrapper()
data = virtuoso.get(query)

class_counts = {}
predicate_counts = {}

for binding in data["results"]["bindings"]:
    class_uri = binding["class"]["value"]
    subject_count = binding.get("subjectCount", {}).get("value")
    object_count = binding.get("objectCount", {}).get("value")
    predicate_uri = binding.get("p", {}).get("value")

    if subject_count:
        class_counts[class_uri] = int(subject_count)

    if predicate_uri and object_count:
        predicate_counts.setdefault(class_uri, {}).setdefault(predicate_uri, 0)
        predicate_counts[class_uri][predicate_uri] += int(object_count)

total_nodes = sum(class_counts.values())
distinct_classes = len(class_counts)
distinct_predicates = len(predicate_counts.values())

st.subheader("Data Summary")
st.write("Total Nodes:", total_nodes)
st.write("Distinct Classes:", distinct_classes)
st.write("Distinct Predicates:", distinct_predicates)

st.subheader("Class Distribution")
st.bar_chart(class_counts)

st.subheader("Predicate Distribution")

# Create data for the bar chart
predicate_labels = list(predicate_counts.keys())
predicate_values = list(predicate_counts.values())

# Generate the bar chart using Streamlit's charting capabilities
st.bar_chart(predicate_counts)

st.subheader("Top Classes by Node Count")
sorted_classes = sorted(class_counts.items(), key=lambda x: x[1], reverse=True)
for class_uri, count in sorted_classes:
    st.write("Class:", class_uri)
    st.write("Count:", count)

st.write("Top Predicates by Count within Each Class:")
for class_uri, predicates in predicate_counts.items():
    st.write("Class:", class_uri)
    for predicate_uri, count in predicates.items():
        st.write("Predicate:", predicate_uri)
        st.write("Count:", count)
    st.write("-" * 20)
