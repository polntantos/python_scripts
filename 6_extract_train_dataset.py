from classes.VirtuosoWrapper import VirtuosoWrapper
from spacy.tokens import DocBin
from spacy.training import Example
import spacy
from spacy.training import biluo_tags_to_offsets
import random

query = """
SELECT ?title ?attribute_label STRAFTER(str(?has_attribute), "#") as ?label
WHERE {
  ?product a <http://magelon.com/ontologies/products> .
  ?product <http://magelon.com/ontologies/products#title> ?title.
  ?attribute a <http://magelon.com/ontologies/attributes>.
  ?product ?has_attribute ?attribute.
  ?attribute rdfs:label ?attribute_label.
  FILTER NOT EXISTS{?product <http://magelon.com/ontologies/has_attribute#uknown> ?attribute}
}
"""
virtuoso = VirtuosoWrapper()
response = virtuoso.getAll(query)

title_features_dict = {}

for row in response:
  if row["title"] not in title_features_dict:
    title_features_dict[row["title"]]=[]
  attribute = (
    row["attribute_label"],
    row["label"]
  )
  if attribute not in title_features_dict[row["title"]]:
    title_features_dict[row["title"]].append(attribute)
# config = spacy.util.train_config(n_iter=100, learning_rate=0.01)

nlp = spacy.blank("en")
nlp.add_pipe("ner")
db = DocBin() # create a DocBin object 

def get_biluo_tags(product_title,attributes):
    attribute_dict = {}
    for attribute,attribute_name in attributes:
      attribute_parts=attribute.split()
      attribute_labels=[]
      for part in attribute_parts:
        if(part in attribute_dict):
          continue
        else:
          attribute_labels.append(part)
      if len(attribute_labels)>1:
        # print(attribute_labels)
        for index,label in enumerate(attribute_labels):
          if(index==0):
            attribute_dict[label]=f"B-{attribute_name.upper()}"
          elif label==attribute_labels[-1]:
            attribute_dict[label]=f"L-{attribute_name.upper()}"
          else:
            attribute_dict[label]=f"I-{attribute_name.upper()}"
      elif(attribute_labels):
        attribute_dict[attribute_labels[0]]=f"U-{attribute_name.upper()}"
    biluo_tags = []
    open_tag=False
    for word in product_title.split():
        if word.lower() in attribute_dict:
          tag=attribute_dict[word.lower()]
          if("B-" in tag):
            open_tag=True
            biluo_tags.append(tag)
          elif("L-" in tag and open_tag):
            open_tag=False
            biluo_tags.append(tag)
        else:
          biluo_tags.append('O')
    return biluo_tags

optimizer = nlp.initialize()

examples = []
for title,product_info in title_features_dict.items():
  title_doc=nlp(title)
  biluo = get_biluo_tags(title,product_info)
  entities = biluo_tags_to_offsets(title_doc,biluo)
  if(entities==[]):
    continue
  print(title)
  print(entities)
  example = Example.from_dict(title_doc,{"entities":entities})
  examples.append(example)

nlp = spacy.blank("en")
nlp.begin_training()
random.shuffle(examples)
n=5
for i in range(0,len(examples),n):
    batch = examples[i:i+n]
    nlp.update(batch,sgd=optimizer)

nlp.to_disk("./output")

sample_products=random.sample(response,10)
for product in sample_products:
  doc = nlp(product['title'])
  print(product['title'])
  for entity in doc.ents:
    print(entity)

nlp_ner = spacy.load("./model-best")


#python3 -m spacy init config config.cfg --lang en --pipeline ner --optimize efficiency
#python3 -m spacy train config.cfg --output ./ --paths.train ./training_data.spacy --paths.dev ./training_data.sp
# nlp_ner = spacy.load("./model-best")


# nlp.to_disk("model.spacy")

# for product in response:
#   doc = nlp_ner(product['title'])
#   print(product['title'])
#   for entity in doc.ents:
#     print(entity)
  
  # spacy.displacy. (doc, style="dep")

