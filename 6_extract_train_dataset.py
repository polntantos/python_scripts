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
nlp.add_pipe("ner",source=spacy.load("en_core_web_sm"))

def get_biluo_tags(product_title,attributes):
    print(attributes)
    attribute_dict = {}
    for attribute,attribute_name in attributes:
      attribute_parts=attribute.split()
      attribute_labels=[]
      for part in attribute_parts:
        if(part in attribute_dict):
          continue
        else:
          attribute_dict[part]=f"U-{attribute_name.upper()}"
    biluo_tags = []
    for word in product_title.split():
        if word.lower() in attribute_dict:
          tag=attribute_dict[word.lower()]
          biluo_tags.append(tag)
        else:
          biluo_tags.append('O')
    return biluo_tags

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

# nlp = spacy.blank("en")
# nlp.begin_training()

# Create and save a collection of training docs

random.shuffle(examples)
train_examples = examples[len(examples)//2]
test_examples = examples[len(examples)//2:]

train_docbin = DocBin(docs=train_examples)
train_docbin.to_disk("./train.spacy")

n=10
for i in range(0,len(train_examples),n):
    batch = examples[i:i+n]
    nlp.update(batch)

nlp.to_disk("./output")


# Create and save a collection of evaluation docs
dev_docbin = DocBin(docs=test_examples)
dev_docbin.to_disk("./dev.spacy")
for product in test_examples:
  doc = nlp(product['title'])
  print("\n\nTitle")
  print(product['title'])
  print("\nPredictions")
  for entity in doc.ents:
    print(entity.text,entity.label_)

#convert corpora in common formats
# python -m spacy convert ./train.gold.conll ./corpus

# nlp_ner = spacy.load("./model-best")


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

