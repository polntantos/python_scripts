from classes.VirtuosoWrapper import VirtuosoWrapper
from spacy.tokens import DocBin
from spacy.training import Example
import spacy
import random

query = """
SELECT ?brand ?brandName
WHERE {
  ?brand a <http://omikron44/ontologies/brands> .
  ?brand <http://omikron44/ontologies/brands#brand> ?brandName.
  OPTIONAL {
    ?brand <http://omikron44/ontologies/brand#refers> ?otherBrand .
  }
  FILTER (!BOUND(?otherBrand))
} ORDER BY ?brand
"""
virtuoso = VirtuosoWrapper()
masterBrands = virtuoso.getAll(query)

brandNames = [brand['brandName'] for brand in masterBrands]
brandLinks = [brand['brand'] for brand in masterBrands]

# config = spacy.util.train_config(n_iter=100, learning_rate=0.01)

nlp = spacy.blank("en")
nlp.add_pipe("ner")
db = DocBin() # create a DocBin object 

query = """
SELECT ?title ?brandName
WHERE {
  ?product a <http://omikron44/ontologies/products> .
  ?product <http://omikron44/ontologies/products#title> ?title.
  ?brand a <http://omikron44/ontologies/brands>.
  ?brand <http://omikron44/ontologies/brands#brand> ?brandName.
  ?product <http://omikron44/ontologies/products#brand> ?brand.
}
"""
products = virtuoso.getAll(query=query)

def entity_list_creator(title,brand):
  brand_encoding = []
  for word in title.split():
    if word == brand:
      brand_encoding.append("U-ORG")
    else:
      brand_encoding.append("O")
  return brand_encoding

optimizer = nlp.initialize()

examples = []
for product_info in products:
  entities = entity_list_creator(product_info['title'],product_info['brandName'])
  if "U-ORG" not in entities:
    continue
  example = Example.from_dict(nlp.make_doc(product_info['title']),{"entities":entities})
  examples.append(example)
  if len(examples)>1000:
    print("updating")
    nlp.update(examples,sgd=optimizer)
    examples = []

if(len(examples)!=0):
  nlp.update(examples,sgd=optimizer)

nlp.to_disk("/output")

sample_products=random.sample(products,10)
for product in sample_products:
  doc = nlp(product['title'])
  print(product)
  for entity in doc.ents:
    print(entity)

# # training_data = []
# for brandName in brandNames:
#   if brandName !='' and brandName != None:
#     print(f"brandName : len {len(brandName)} : {type(brandName)}")
#     doc = nlp.make_doc(brandName)
#     ents = []
#     span = doc.char_span(0,len(brandName),"BRAND",alignment_mode="contract")
#     print(span)
#     ents.append(span)
#     doc.ents=ents
#     db.add(doc=doc)

db.to_disk("./training_data.spacy")
#python3 -m spacy init config config.cfg --lang en --pipeline ner --optimize efficiency
#python3 -m spacy train config.cfg --output ./ --paths.train ./training_data.spacy --paths.dev ./training_data.sp
nlp_ner = spacy.load("./model-best")


# nlp.to_disk("model.spacy")

for product in products:
  doc = nlp_ner(product['title'])
  print(product['title'])
  for entity in doc.ents:
    print(entity)
  
  # spacy.displacy. (doc, style="dep")

