import spacy
from classes.VirtuosoWrapper import VirtuosoWrapper
import re
import nltk
from nltk.corpus import stopwords
from rdflib import Graph, URIRef, RDF, RDFS, Literal
from slugify import slugify
import click


nltk.download("stopwords")

def get_data(brand_name):
    query = f"""
    SELECT ?product ?product_title ?mpn ?merchant_id
    WHERE {{
    ?product <http://magelon.com/ontologies/products#brand> ?brand_uri ;
            <http://magelon.com/ontologies/products#title> ?product_title .
            ?product <http://magelon.com/ontologies/products#mpn> ?mpn.
            OPTIONAL{{?product <http://magelon.com/ontologies/products#merchant_id> ?merchant_id }}
    {{
        Select ?brand_uri ?brand_name
        WHERE {{
        {{
        ?brand_uri ?p "{brand_name}".
        ?brand_uri <http://magelon.com/ontologies/brands#brand> ?brand_name.
        ?brand_uri a <http://magelon.com/ontologies/brands>.
        }}
        UNION
        {{
        ?b ?n "{brand_name}".
        ?brand_uri ?refers ?b.
        ?brand_uri <http://magelon.com/ontologies/brands#brand> ?brand_name.
        ?brand_uri a <http://magelon.com/ontologies/brands>.
        }}
        }}
    }}
    }}
    """
    virtuoso = VirtuosoWrapper()
    response = virtuoso.getAll(query)
    return response

def create_rdf_graph(product_dict):
    graph = Graph()
    className = URIRef("http://magelon.com/ontologies/attributes")
    for product_uri, product_data in product_dict.items():
        if "brand" in product_data.keys():
            graph.add(
                (
                    URIRef(product_uri),
                    URIRef("http://magelon.com/ontologies/has_attribute#brand"),
                    URIRef(
                        base="http://magelon.com/ontologies/attribute/",
                        value=slugify(product_data["brand"]),
                    ),
                )
            )
            graph_add_class(
                graph,
                URIRef(
                    base="http://magelon.com/ontologies/attribute/",
                    value=slugify(product_data["brand"]),
                ),
                className,
            )
        if "product_number" in product_data.keys():
            graph.add(
                (
                    URIRef(product_uri),
                    URIRef(
                        "http://magelon.com/ontologies/has_attribute#product_number"
                    ),
                    URIRef(
                        base="http://magelon.com/ontologies/attribute/",
                        value=slugify(product_data["product_number"]),
                    ),
                )
            )
            graph_add_class(
                graph,
                URIRef(
                    base="http://magelon.com/ontologies/attribute/",
                    value=slugify(product_data["product_number"]),
                ),
                className,
            )
        if "colors" in product_data.keys():
          for color in product_data["colors"]:
            graph.add(
                (
                    URIRef(product_uri),
                    URIRef("http://magelon.com/ontologies/has_attribute#color"),
                    URIRef(
                        base="http://magelon.com/ontologies/attribute/",
                        value=slugify(color),
                    ),
                )
            )
            graph_add_class(
                graph,
                URIRef(
                    base="http://magelon.com/ontologies/attribute/",
                    value=slugify(color),
                ),
                className,
            )
        if "attributes" in product_data.keys():
            for feature in product_data["attributes"]:
                graph.add(
                    (
                        URIRef(product_uri),
                        URIRef("http://magelon.com/ontologies/has_attribute#uknown"),
                        URIRef(
                            base="http://magelon.com/ontologies/attribute/",
                            value=slugify(feature),
                        ),
                    )
                )
                graph_add_class(
                    graph,
                    URIRef(
                        base="http://magelon.com/ontologies/attribute/",
                        value=slugify(feature),
                    ),
                    className,
                )
                graph.add(
                    (
                        URIRef(
                            base="http://magelon.com/ontologies/attribute/",
                            value=slugify(feature),
                        ),
                        RDFS.label,
                        Literal(feature),
                    )
                )

    return graph


def graph_add_class(graph: Graph, s, o):
    graph.add((s, RDF.type, o))


choises = [
    "Apple",
    "Lenovo",
    "Xiaomi",
    "Dell",
    "Toshiba",
    "Asus",
    "MSI",
    "Acer",
    "Gigabyte",
    "LG",
    "Razer",
    "Intel",
    "AMD",
]

@click.command()
@click.option(
    "--brand",
    default=",".join(choises),
    prompt=f"Select a brand(s) to extract features from (seperate by comma for many)",
)
def export_brand_features(brand):
  color_query = """
      select ?color_uri ?label
      where { 
      {?color_uri a <http://magelon.com/ontologies/colors>.}
      UNION
      {?color_uri a <http://omikron44/ontologies/mixture_colors>.}
      UNION
      {?color_uri a <http://magelon.com/ontologies/color_variations>.}
      ?color_uri <http://www.w3.org/2000/01/rdf-schema#label> ?label.
      }
  """
  virtuoso = VirtuosoWrapper()
  response_colors = virtuoso.getAll(color_query)
  colors = set([row["label"].lower() for row in response_colors])

  brand_names = brand.split(",")
  click.echo(brand_names)
  for brand_name in brand_names:
    # brand = "Lenovo"
    response = get_data(brand_name)
    # product_titles = [row["product_title"] for row in response]
    mpns = set([row["mpn"].lower() for row in response])

    nlp = spacy.blank("en")

    vocab = {}
    followers ={}
    product_dict={}
    for row in response:
      title = row["product_title"]
      product_attributes={"title":title.lower() ,"attributes":[]}
      doc = nlp(title)
      previous_word = ""
      for token in doc:
        if re.match(r"[>#+'?&;:,$%\\^*®™()]+|-",token.text):
          continue
        if re.match(r"[\n\t]+",token.text):
          continue
        word=token.text.lower()
        if word in stopwords.words("english"):
          continue
        if word in mpns:
          product_attributes["product_number"]=word
          previous_word=""
          continue
        if word == brand_name.lower():
          product_attributes["brand"]=word
          previous_word=""
          continue
        if word in colors:
          if("colors" not in product_attributes.keys()):
            product_attributes["colors"]=[]
          product_attributes["colors"].append(word)
        if word not in vocab.keys():
          vocab[word]=0
        vocab[word]=vocab[word]+1
        product_attributes["attributes"].append(word)
        if previous_word!= "" and previous_word!=word: 
          if previous_word not in followers.keys():
            followers[previous_word]={}
          if word not in followers[previous_word].keys():
            followers[previous_word][word] = 0
          followers[previous_word][word]=followers[previous_word][word]+1
        previous_word = word
      product_dict[row["product"]]=product_attributes

    print(f"{len(product_dict.keys())}\t: {brand_name} products")
    # possible features by probability 
    possible_features={}
    for word in vocab:
      possible_features[word]=[]

    for word in vocab.keys():
      if word in [" ","\n","\t"]: ## because there are many occasions of corrupted data
        continue
      if word in followers.keys() and len(followers[word])==1:
        only_word=list(followers[word].keys())[0]
        possible_features[word].append(" ".join([word,only_word]))
      if word in followers.keys() and len(followers[word])>1:
        highest_key = max(followers[word], key=lambda key: followers[word][key])
        possible_features[word].append(" ".join([word,highest_key]))
        for follower,appearances in followers[word].items():
          if appearances == vocab[follower]:
            possible_features[follower].append(" ".join([word,follower]))

    print(f"{len(possible_features.keys())}\t: possible features")

    for product_uri,product_data in product_dict.items():
      for attribute in product_data["attributes"]:
        if attribute in possible_features.keys():
          for possible_feature in set(possible_features[attribute]):
            parts = possible_feature.split()
            if len(parts)<2:
              continue
            if parts[0] in product_data["title"] and parts[1] in product_data["title"]:
              product_dict[product_uri]["attributes"].append(possible_feature)

    graph = create_rdf_graph(product_dict)
    virtuoso.save(graph)


if __name__ == "__main__":
    export_brand_features()