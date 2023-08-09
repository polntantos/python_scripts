def evaluate_strings(string):
    score = 0
    # Rule 1: Prefer string with ' symbol
    if "'" in string:
        score += 1
    # Rule 2: Prefer string with fewer symbols (excluding dots)
    symbol_count = sum(1 for char in string if char.isalpha() or char.isspace())
    dot_count = string.count('.')
    score -= symbol_count - dot_count
    # Rule 3: Prefer string with one word before/after dot
    if dot_count > 0:
        words = string.split(' ')
        for word in words:
            if '.' in word and len(word.split('.')) > 2:
                score -= 1
    # Rule 4: Prefer string with series format (e.g., separated by ':')
    if ':' in string and len(string.split(':')) > 2:
        score += 1
    return score

brand_names = [
  "Crafters Companion",
  "Crafter's Companion",
  "friends",
  "F.R.I.E.N.D.S",
  "Disney Pixar",
  "Disney-Pixar",
  "Arsenal FC",
  "Arsenal F.C.",
  "Avengers Infinity War",
  "Avengers: Infinity War",
  "A.P.C.",
  "APC",
  "Fisher Price",
  "Fisher-Price"
]

for name in brand_names:
  print(name,evaluate_strings(name))