import spacy

nlp = spacy.load("./output/model-best/")
doc = nlp("iPhone 11 vs iPhone 8: What's the difference?")
print(doc.ents)