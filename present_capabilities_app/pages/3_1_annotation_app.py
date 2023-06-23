import streamlit as st
import json


def get_previous_annotations(title, annotations):
    """
    Retrieve previously annotated strings from other titles.
    """
    previous_annotations = []
    for annotation in annotations:
        # if annotation["title"] != title:
        previous_annotations.extend(annotation["annotations"])
    return previous_annotations


def get_previous_annotation(word, previous_annotations):
    """
    Check if the given word has been previously annotated.
    If found, return the corresponding annotation.
    """
    for annotation in previous_annotations:
        if annotation["word"] == word:
            return annotation

    return None


def annotate_text(title, annotations):
    st.subheader("Text Annotation Tool")
    st.write("Title: ", title)

    # Check if the current title has any previously annotated strings
    previous_annotations = get_previous_annotations(title, annotations)
    # print(previous_annotations)
    target_string = title
    for pre_annotation in previous_annotations:
        if (
            pre_annotation["word"] in target_string
            and pre_annotation["word"] + "," not in target_string
            and not target_string.endswith(pre_annotation["word"])
        ):
            target_string = target_string.replace(
                pre_annotation["word"], pre_annotation["word"] + ","
            )
    # target_string  = target_string.replace('-', ",-,")
    text = st.text_input(
        "Enter the text(split by comma , ):", target_string, key="markup_input"
    )

    if text:
        title_annotations = {}
        title_annotations["title"] = title
        title_annotations["annotations"] = []

        st.subheader("Annotate Words")
        words = [word.strip() for word in text.split(",")]

        for word in words:
            annotated_word = {}
            annotation_word = word.strip("-").strip()
            annotated_word["word"] = annotation_word

            # Check if the word has been previously annotated
            previous_annotation = get_previous_annotation(
                annotation_word, previous_annotations
            )
            print(previous_annotation)
            if previous_annotation:
                tag = previous_annotation["tag"]
                tag = st.text_input(f"Tag for '{annotation_word}':", value=tag)
                annotated_word["tag"] = tag
            else:
                tag = st.text_input(f"Tag for '{annotation_word}':")

            annotated_word["tag"] = tag
            if tag:
                title_annotations["annotations"].append(annotated_word)

        annotations.append(title_annotations)

    if st.button("Save"):
        with open("app_annotations.json", "w") as f:
            json.dump(annotations, f)
        st.success("Annotations saved to annotations.json.")


# Main code
def main():
    st.title("Text Annotation Tool")

    with open("prepared-clusters.json") as f:
        json_data = json.load(f)

    with open("app_annotations.json") as ann:
        try:
            annotations = json.load(ann)
        except:
            annotations = []

    if 'index' not in st.session_state:
        st.session_state.index = 0
        
        
    cluster_keyes = [cluster_key for cluster_key in json_data.keys()]
    selected_cluster = st.selectbox("Select cluster", options=cluster_keyes,index=st.session_state.index)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Previous") and st.session_state.index > 0:
            st.session_state.index -= 1

    with col2:
        st.write("")  # Empty column to provide spacing

    with col3:
        if st.button("Next") and st.session_state.index < len(cluster_keyes) - 1:
            st.session_state.index += 1
    if selected_cluster:
        titles = [product["title"] for product in json_data[selected_cluster]]
        selected_title = st.selectbox("Select a title:", titles)

        if selected_title:
            for item in annotations:
                if item['title'] == selected_title:
                    st.write('Annotated!')
                    break
            annotate_text(selected_title, annotations)


if __name__ == "__main__":
    main()
