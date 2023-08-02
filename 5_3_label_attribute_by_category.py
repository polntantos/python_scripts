from classes.VirtuosoWrapper import VirtuosoWrapper
import json
import re

def group_by_similarity_regex(array):
    teams = []
    while array:
      item = array.pop()
      team = []
      regex = ""
      for char in item:
          if char.isalpha():
              regex += char
          elif char.isdigit():
              regex += "\\d"
          else:
              regex += r"\s"

      for other_item in array:
          if item == other_item:
              continue
          if item in team or other_item in team:
              continue
          match = re.match(regex, other_item)
          if match:
              team.append(other_item)
      # array.remove(item)
      if team != []:
        teams.append(team)

    return teams

categories_query = """
SELECT DISTINCT ?google_product_type ?label
where{
?product a <http://magelon.com/ontologies/products>;
           <http://magelon.com/ontologies/products#google_product_type> ?google_product_type.
?google_product_type rdfs:label ?label.
}
"""
virtuoso = VirtuosoWrapper()
categories_result = virtuoso.getAll(categories_query)

categories_dict = {}
category_labels = []
for row in categories_result:
  categories_dict[row["label"]]=row["google_product_type"]
  category_labels.append(row["label"])
  
print("Available categories")
for index,category in enumerate(category_labels):
  print(f"{index} \t:{category}")
  
category_selection = input("Select category to label: ")

print(f"selected {category_labels[int(category_selection)]}")

selected_category_uri = categories_dict[category_labels[int(category_selection)]]

category_attributes_query=f"""
SELECT COUNT(?attribute) as ?attribute_hits ?attribute  ?label
where{{
?attribute a <http://magelon.com/ontologies/attributes>;
                     rdfs:label ?label.
?product a <http://magelon.com/ontologies/products>;
           <http://magelon.com/ontologies/products#google_product_type> <{selected_category_uri}>;
           <http://magelon.com/ontologies/has_attribute#uknown> ?attribute.
}}GROUP BY ?attribute ?label
ORDER BY DESC(?attribute_hits)
"""

attributes_array = virtuoso.getAll(category_attributes_query)
attributes = [row["label"] for row in attributes_array]

attribute_teams = group_by_similarity_regex(attributes)
print(attribute_teams)
print(len(attribute_teams))
label_input=input("What are you labeling?(split by , ): ")
labels = label_input.split(",")

labeled_teams = {}

for team in attribute_teams:
  for attribute in team:
    print(attribute)
  for index,label in enumerate(labels):
    print(f"{index}:{label}")
  label_selection=input("Select label for attributes(leave empty for skipping):")
  if(label_selection!="" and int(label_selection) in range(0,len(labels)+1)):
    selected_label=labels[int(label_selection)]
    print(labels)
    print(labels[int(label_selection)])
    print(selected_label)
    if selected_label not in labeled_teams.keys():
      labeled_teams[selected_label]=[]
    labeled_teams[selected_label].append(team)
  with open(f"storage/{category_labels[int(category_selection)]}_labeled_attribute_teams.json", "w") as json_file:
    print(labeled_teams)
    json.dump(labeled_teams, json_file)