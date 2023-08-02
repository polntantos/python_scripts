from classes.VirtuosoWrapper import VirtuosoWrapper
import json
import re
import os


def get_files_with_extension(extension):
    files = []
    for root, directories, filenames in os.walk(".", topdown=True):
        for filename in filenames:
            if filename.endswith(extension):
                files.append(os.path.join(root, filename))
    return files


def prepare_query(label, value):
    query = f"""
    DELETE {{
      ?product <http://magelon.com/ontologies/has_attribute#uknown> ?attribute .
    }}
    INSERT {{
      ?product <http://magelon.com/ontologies/has_attribute#{label}> ?attribute .
    }}
    WHERE {{
      ?product a <http://magelon.com/ontologies/products>;
              <http://magelon.com/ontologies/has_attribute#uknown> ?attribute.
      ?attribute a <http://magelon.com/ontologies/attributes>;
            rdfs:label "{value}" .
    }}
    """
    return query


def perform_attribute_team_labeling(file_path):
    virtuoso = VirtuosoWrapper()
    with open(file_path, "r") as json_file:
        teams = json.load(json_file)
        for label, team in teams.items():
            value_list = []
            for group in team:
                value_list.extend(group)
            for value in set(value_list):
                clean = re.sub(r'[\'"]', "", value)
                update_query = prepare_query(label, clean)
                print(update_query)
                virtuoso.get(update_query)


files = get_files_with_extension("labeled_attribute_teams.json")
print("Available files")
for index, file_path in enumerate(files):
    print(f"{index}\t:{file_path}")

file_selection = input("Select file to save labels (leave empty for all files) :")

if file_selection == "":
    for file in files:
        perform_attribute_team_labeling(file)
elif int(file_selection) in range(0, len(files) + 1):
    selected_file = files[int(file_selection)]
    print(f"Importing {selected_file}")
    perform_attribute_team_labeling(selected_file)
else:
    print("Bad option")
