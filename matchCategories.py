import json
import re

from sklearn.metrics import jaccard_score

# Read the Google categories file
print('Opening google categories')
with open('googleToGraph/categories.txt', 'r') as file:
    google_categories = {}
    for line in file:
        line = line.strip().split(' - ')
        category_id = line[0]
        category_path = line[1]
        google_categories[category_id] = category_path

# Read the category clusters file
with open('clusters/category-clusters.json', 'r') as file:
    print('Opening merchant categories')
    category_clusters = json.load(file)

# # Tokenize the Google category keywords
# tokenized_google_categories = {}
# print('Tokenizing google categories')
# for category_id, category_path in google_categories.items():
#     tokens = re.findall(r'\b\w+\b', category_path.lower())
#     tokenized_google_categories[category_id] = tokens

# Assign merchant category clusters to Google categories by keyword matching
assigned_clusters = {}
print('Assigning categories')
for cluster_id, cluster_categories in category_clusters.items():
    assigned_clusters[cluster_id] = []
    for category in cluster_categories:
        print(category)
        best_match = None
        best_score = 0
        for category_id, category_path in google_categories.items():
            # print(category_id, category_path)
            # score = jaccard_score(
            #   set(category.lower().split(' > ')),
            #   set(category_path.lower().split(' > ')),
            #   # average='weighted'
            #   )
            
            set1=set(category.lower().split(' > '))
            set2=set(category_path.lower().split(' > '))
            intersection = set1.intersection(set2)
            union = set1.union(set2)
            score = len(intersection) / len(union)
            if score > best_score:
                best_match = category_id
                best_score = score
        if best_match:
            # print('Appending category')
            assigned_clusters[cluster_id].append(
              {
                "Merchant Category": category,
                "Google Category Path": google_categories[best_match],
                "Google Category ID": best_match,
                "Similarity Score": best_score
              }
            )

        
output_file = 'clusters/assigned_clusters.json'
print('Saving categories')
with open(output_file, 'w') as file:
    json.dump(assigned_clusters, file, indent=4)

print(f"Results saved to {output_file}")