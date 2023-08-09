import spacy

nlp = spacy.load("./output/model-best/")

test_titles = [
  "Intel Core i7 12700K 3.50GHz Socket LGA1700 CPU/Processor",
  "Toshiba Tecra A50-C-217 39.6 cm (15.6\") LCD Notebook - Intel Core i5 (6th Gen) i5-6200U Dual-core",
  "Apple iPhone 13 Mini 256GB Starlight"
]
for test_title in test_titles:
  doc = nlp(test_title)
  print(test_title)
  print("\n")
  for ent in doc.ents:
    print(ent.label_, ent.text)
  print("\n")