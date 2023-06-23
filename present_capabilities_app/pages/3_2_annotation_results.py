import streamlit as st
import json
import spacy
from spacy.training import Example

# Load the JSON data from the file
with open("app_annotations.json", "r") as f:
    json_data = json.load(f)

# Process the JSON data and generate the desired format
processed_data = []
for item in json_data:
    title = item["title"]
    annotations = item["annotations"]
    annotated_text = []
    for annotation in annotations:
        word = annotation["word"]
        tag = annotation["tag"]
        start = title.find(word)
        end = start + len(word)
        annotated_text.append((start, end, tag.upper()))
    # formatted_annotations = [(ann["word"], ann["tag"].upper()) for ann in annotations]
    # processed_data.append((title, formatted_annotations))
    processed_data.append((title, annotated_text))

# Train the NER model with spaCy
nlp = spacy.blank("en")  # Create a blank spaCy model
# ner = nlp.create_pipe()
nlp.add_pipe("ner",source=spacy.load("en_core_web_sm"))
# nlp.add_pipe("tok2vec") 
# st.write(type(nlp))
for title, annotations in processed_data:
    doc = nlp.make_doc(title)
    entities = [
        (start, end, label) for (start, end, label) in annotations
    ]
    example =Example.from_dict(doc,{"entities":entities}) #spacy.training.GoldParse(doc, entities=entities)
    # st.write(example.to_dict())
    nlp.update([example])

model_output_path = "models"
nlp.to_disk(model_output_path)


# Display the processed data
for data in processed_data:
    title, annotations = data
    st.write(title)
    st.write(annotations)
    st.write('Predicted data')
    doc = nlp(title)
    st.write(doc)
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    st.write(entities)

# Display the processed data
# for data in processed_data:
#     title, annotations = data
#     st.write(title)
#     st.write(annotations)