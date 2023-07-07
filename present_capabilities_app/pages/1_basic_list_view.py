import streamlit as st
from classes.VirtuosoWrapper import VirtuosoWrapper

st.set_page_config(page_title="Basic List View", page_icon="📊", layout="wide")

st.header("Basic List View")
if "triples_page" not in st.session_state:
    st.session_state["triples_page"] = 0
    st.session_state["previous_page"] = False
    st.session_state["next_page"] = 1


ex1, ex2 = st.columns(2)


def get_all_resource_types():
    query = "select distinct ?Concept where {[] a ?Concept} LIMIT 100"
    virtuoso = VirtuosoWrapper()
    result = virtuoso.get(query)
    concepts = [row["Concept"]["value"] for row in result["results"]["bindings"]]
    return concepts


def get_resource_type_predicates(resource_type):
    query = f"""
        SELECT DISTINCT ?predicate
        WHERE {{
        ?subject a <{resource_type}> .
        ?subject ?predicate ?object .
    }}"""
    virtuoso = VirtuosoWrapper()
    result = virtuoso.get(query)
    concepts = [row["predicate"]["value"] for row in result["results"]["bindings"]]
    return concepts


def get_next_page():
    st.session_state["triples_page"] += 1


def get_prev_page():
    st.session_state["triples_page"] -= 1


def get_triples(page=0):
    resource_type = st.session_state["select_concept"]
    predicates = st.session_state["selected_predicate"]
    offset = page * 20
    select_part = ""
    where_part = ""
    st.session_state["predicate_dict"] = {}
    for predicate in predicates:
        predicate_name = predicate.split("#", 1)[1].replace("-", "")
        select_part += (
            f""" GROUP_CONCAT(?{predicate_name}; separator=", ") AS ?{predicate_name}"""
        )
        where_part += f"OPTIONAL{{?s <{predicate}> ?{predicate_name}.}}"
        st.session_state["predicate_dict"][predicate_name] = predicate

    query = f"""
        SELECT ?s {select_part}
        WHERE{{
            ?s a <{resource_type}> .
            {where_part}
        }}
        ORDER BY ?s 
        OFFSET {offset} LIMIT 20
    """
    virtuoso = VirtuosoWrapper()
    result = virtuoso.get(query)
    response_keys = result["head"]["vars"]
    triples = []
    for row in result["results"]["bindings"]:
        value_row = {}
        for key in response_keys:
            if key in row:
                value_row[key] = row[key]["value"]
        triples.append(value_row)
    st.session_state["triples_page"] = page

    if len(triples) >= 20:
        st.session_state["next_page"] = page + 1
    else:
        st.session_state["next_page"] = None

    if page > 0:
        st.session_state["previous_page"] = page - 1
    else:
        st.session_state["previous_page"] = None
    return triples


def store_triple():
    updateItems = []
    for item in st.session_state:
        if "FormSubmitter" in item:
            id = item.strip("FormSubmitter:form:").strip("-Save")
        if "-label" in item:
            updateItems.append(
                {
                    "predicate_key": item.split("-label:")[1],
                    "predicate_value": st.session_state[item],
                }
            )
    if id is not None:
        delete_value = ""
        insert_value = ""
        for item in updateItems:
            delete_value += f"<{id}> <{st.session_state['predicate_dict'].get(item['predicate_key'])}> ?{item['predicate_key']}."
            insert_value += f"<{id}> <{st.session_state['predicate_dict'].get(item['predicate_key'])}> '{item['predicate_value']}'."

        updateQuery = f"""
            DELETE{{
                {delete_value}
            }}
            INSERT{{
                {insert_value}
            }}
            WHERE{{
                {delete_value}
            }}
        """
        print(updateQuery)
        # exit()
        virtuoso = VirtuosoWrapper()
        response = virtuoso.send(updateQuery)
        print(response)
        if response["status"] == "success":
            st.success(response["result"], icon="✅")
        else:
            st.error(response["result"], icon="🚨")


# extenders with query desc
with ex1:
    with st.expander("Concept query"):
        st.write(
            """select distinct ?Concept where {[] a ?Concept} LIMIT 100
            This query is the first thing we see when we open virtuoso sparql endpoint
            Leaving it unchanged we also used it here to present a list of resource types for the user to choose.
        """
        )

with ex2:
    with st.expander("Predicates query"):
        st.write(
            """SELECT DISTINCT ?predicate
                WHERE {
                    ?subject a <resource_type> .
                    ?subject ?predicate ?object .
                    }
            Now this query is a bit more complex but it can still be used in a function with variables to filter results.
            More specifically it implies the logic that we will get all values of possible predicates for the resource_type the user selected and we will return them for the user to choose.
        """
        )


sel1, sel2 = st.columns(2)
with sel1:
    concepts = get_all_resource_types()
    st.selectbox("Select resource to list", options=concepts, key="select_concept")
with sel2:
    if (
        "select_concept" in st.session_state
        and st.session_state["select_concept"] != ""
    ):
        predicates = get_resource_type_predicates(st.session_state["select_concept"])
    else:
        predicates = []

    st.multiselect(
        "Select a predicate to list", options=predicates, key="selected_predicate"
    )

box = st.empty()
with box.container():
    if (
        "select_concept" in st.session_state
        and st.session_state["select_concept"] != ""
        and "selected_predicate" in st.session_state
        and st.session_state["selected_predicate"] != ""
    ):
        page = (
            st.session_state["triples_page"]
            if "triples_page" in st.session_state
            else 0
        )
        triples = get_triples(page)
        for triple in triples:
            cols = st.columns(len(st.session_state["selected_predicate"]) + 2)
            with st.container():
                for name, item in triple.items():
                    colnum = list(triple).index(name)
                    with cols[colnum]:
                        st.write(item)

                with cols[len(cols) - 1]:
                    disabled = False
                    if len(triple.items()) < 2:
                        disabled = True
                    editButton = st.button(
                        label="Edit", key=triple["s"], type="primary", disabled=disabled
                    )
                    if editButton:
                        with st.form(key=f"form:{triple['s']}"):
                            for name, item in triple.items():
                                if name != "s":
                                    st.text_input(
                                        label=name,
                                        value=item,
                                        key=f"form:id:{triple['s']}-label:{name}",
                                    )
                            st.form_submit_button("Save", on_click=store_triple)

prev_col, next_col = st.columns(2)

with prev_col:
    disabled = True

    if st.session_state["previous_page"] != None:
        disabled = False
    st.button(
        "Previous",
        "previous",
        disabled=disabled,
        on_click=get_prev_page,
    )

with next_col:
    disabled = True
    if st.session_state["next_page"] != None:
        disabled = False
    st.button("Next", "next", on_click=get_next_page)
