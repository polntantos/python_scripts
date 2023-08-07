from classes.VirtuosoWrapper import VirtuosoWrapper
from spacy.tokens import DocBin,Span
from spacy.training import Example
from spacy.matcher import PhraseMatcher
from spacy import Span
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

nlp = spacy.blank("en")
nlp.add_pipe("ner",source=spacy.load("en_core_web_sm"))

product_titles=[row["title"] for row in response]

product_word_meaning = {}

for row in response:
  p_name=row["title"]
  if(p_name not in product_word_meaning.keys()):
    product_word_meaning[p_name]={}
  attribute = row["label"]  
  for word in row["attribute_label"].split():
    product_word_meaning[p_name][word]=attribute

#Create matchers and extract spans according to documentation

# for key,values in label_dict.items():
#   print(key,patterns)

docs=[]

for title in product_titles:
  doc = nlp(title.lower())
  values=product_word_meaning[title]
  patterns = {}
  for attribute,label in values.items():
    if label not in patterns.keys():
      patterns[label]=[]
    patterns[label].append(nlp.make_doc(attribute))
  for label,pattern_values in patterns.items():
    matcher = PhraseMatcher(nlp.vocab)
    matcher.add(label,pattern_values)
  matches = matcher(doc)
  print(f"Found {len(matches)} matches")
  spans = [Span(doc, start, end, label=match_id) for match_id, start, end in matches]
  doc.ents = spans
  docs.append(doc)

doc_bin = DocBin(docs=docs)
doc_bin.to_disk("./train.spacy")