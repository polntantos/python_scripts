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
        st.session_state["actions"] = actions_from_file

    except:
        st.session_state["actions"] = {}


def get_next():
    save_state()
    current_key = st.session_state["cur_key"]
    dictionary = st.session_state["brand_clusters"]
    keys = sorted(map(int, dictionary.keys()))
    current_index = keys.index(int(current_key))
    next_index = (current_index + 1) % len(keys)
    next_key = str(keys[next_index])
    st.session_state["cur_key"] = next_key
    st.session_state["cur_item"] = st.session_state["brand_clusters"][str(next_key)]


def get_previous():
    current_key = st.session_state["cur_key"]
    dictionary = st.session_state["brand_clusters"]
    keys = sorted(map(int, dictionary.keys()))
    current_index = keys.index(int(current_key))
    previous_index = (current_index - 1) % len(keys)
    previous_key = str(keys[previous_index])
    st.session_state["cur_key"] = previous_key
    st.session_state["cur_item"] = st.session_state["brand_clusters"][str(previous_key)]


def save_state():
    action_dict = {}
    for key in st.session_state:
        if "wtd" in key:
            action_item = key.split("+")[0]
            if action_item not in action_dict:
                action_dict[action_item] = {}
            action_dict[action_item]["wtd"] = st.session_state[key]

        if "sec" in key:
            action_item = key.split("+")[0]
            if action_item not in action_dict:
                action_dict[action_item] = {}
            action_dict[action_item]["sec"] = st.session_state[key]
    st.session_state["actions"][st.session_state["cur_key"]] = action_dict
    state_object = st.session_state["actions"]
    # actions_file = ""

    with open("./pages/data_files/brand_cluster_actions.json", "w") as a:
        json.dump(state_object, a)


if "brand_clusters" not in st.session_state:
    st.session_state["brand_clusters"] = brand_clusters

if "cur_key" not in st.session_state or "cur_item" not in st.session_state:
    max_key = max(st.session_state["actions"].keys(), key=lambda x: int(x))
    st.session_state["cur_key"], st.session_state["cur_item"] = list(
        brand_clusters.items()
    )[int(max_key)]


st.header("Brand validator")
st.write(
    "Cluster number :",
    int(st.session_state["cur_key"]) + 1,
    " of ",
    len(st.session_state["brand_clusters"]),
)
with st.container():
    hcol1, hcol2 = st.columns(2)
    with hcol1:
        st.button("previous", on_click=get_previous)
    with hcol2:
        st.button("next", on_click=get_next)


if st.session_state["cur_key"] not in st.session_state["actions"]:
    st.session_state["actions"][st.session_state["cur_key"]] = {}

##MUST ADD PAGINATION try session state tricks

with st.container():
    for clustered_brand in st.session_state["cur_item"]["brands"].items():
        with st.empty():
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"{clustered_brand[0]}")
                st.write(f"{clustered_brand[1]}")
            with col2:
                options = ["nothing", "validate", "merge_with_valid", "invalidate"]
                preselected_wtd = 0
                if (
                    clustered_brand[1]
                    in st.session_state["actions"][st.session_state["cur_key"]]
                ):
                    preselected_wtd = options.index(
                        st.session_state["actions"][st.session_state["cur_key"]][
                            clustered_brand[1]
                        ]["wtd"]
                    )

                wtd_option = st.selectbox(
                    "what to do",
                    options,
                    key=f"{clustered_brand[1]}+wtd",
                    index=preselected_wtd,
                )
            with col3:
                if wtd_option == "nothing" or wtd_option == "invalidate":
                    select_message = "deactivated"
                    options_arr = []
                    disabled = True
                elif wtd_option == "validate" or wtd_option == "merge_with_valid":
                    if wtd_option == "validate":
                        select_message = "Parent brand"
                    else:
                        select_message = "Select merge brand"
                    brands_to_validate = [""]
                    for key in st.session_state:
                        if (
                            "wtd" in key
                            and clustered_brand[1] not in key
                            and st.session_state[key] == "validate"
                        ):
                            brands_to_validate.append(key.split("+")[0])

                    options_arr = [option for option in brands_to_validate]
                    disabled = False
                preselected_sec = 0
                if (
                    clustered_brand[1]
                    in st.session_state["actions"][st.session_state["cur_key"]]
                ):
                    preselection_item = st.session_state["actions"][
                        st.session_state["cur_key"]
                    ][clustered_brand[1]]
                    if "sec" in preselection_item:
                        if preselection_item["sec"] not in options_arr:
                            options_arr.append(preselection_item["sec"])

                    preselected_sec = options_arr.index(
                        st.session_state["actions"][st.session_state["cur_key"]][
                            clustered_brand[1]
                        ]["sec"]
                    )

                st.selectbox(
                    select_message,
                    options_arr,
                    disabled=disabled,
                    key=f"{clustered_brand[1]}+sec",
                    index=preselected_sec,
                )
    st.button("Save", on_click=save_state)
