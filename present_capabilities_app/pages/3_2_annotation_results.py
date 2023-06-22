import streamlit as st
import json

# Load the JSON data from the file
with open("annotations.json", "r") as f:
    json_data = json.load(f)

# Process the JSON data and generate the desired format
processed_data = []
for item in json_data:
    title = item["title"]
    annotations = item["annotations"]
    formatted_annotations = [(ann["word"], ann["tag"].upper()) for ann in annotations]
    processed_data.append((title, formatted_annotations))

# Display the processed data
for data in processed_data:
    title, annotations = data
    st.write(title)
    st.write(annotations)