Reads
https://www.w3.org/RDF/
https://www.w3.org/2001/sw/wiki/SPARQL
https://www.w3.org/2001/sw/wiki/RDFS
https://neo4j.com/knowledge-graphs-practitioners-guide/
https://networkx.org/documentation/stable/reference/algorithms/community.html#module-networkx.algorithms.community.louvain

Biparte
https://networkx.org/documentation/stable/reference/algorithms/bipartite.html
https://www.geeksforgeeks.org/maximum-bipartite-matching/

Project step by step

Problem:
Έχουμε στα χέρια μας ένα σετ δεδομένων προϊόντων από την βάση του magelon.
Τα δεδομένα αυτά συλλέγονται καθημερινά από διάφορα feed που ανήκουν σε πελάτες προκειμένου να διαφημιστούν στο merchant center της google.
Πέρα από την βασική τους χρήση θέλουμε να δούμε αν μπορούμε να χτίσουμε τις απαραίτητες διαδικασίες ώστε να εξάγουμε μια βάση γνώσης
γύρο από τα προϊόντα και τα χαρακτηριστικά τους με την χρήση αλγόριθμων μηχανικής μάθησης ώστε να καταλήξουμε με δεδομένα κατάληλα για
την εκπαίδευση ενός NLP (Natural Language Processing) μοντέλου μέσω της βιβλιοθήκης spacy για την εξαγωγή λέξεων κλειδιών και την
κατηγοριοποίηση προϊόντων αυτόματα στις κατηγορίες προϊόντων της google.

περιορισμοί
Τα δεδομένα έρχονται σε μορφή (backup).sql από το εργαλείο mysqldump, στην πραγματικότητα δεν θα μπορέσουμε να τραβήξουμε τα δεδομένα από
την πηγή σε μεγάλη κλίμακα καθώς το πλήρες dataset είναι πάνω από 5 δις προϊόντα επομένως θα πρέπει να στήσουμε ένα instance mysql και να φροντίσουμε
να περάσουμε τα δεδομένα μέσα από ένα mapping προκειμένου να τα εκμεταλεύτουμε αλλά και να προσομοιώσουμε τις πραγματικές συνθήκες.
Οι διαδικασίες καθαρισμού και προετιμασίας των δεδομένων περιέχουν αρκετά metadata για να εκφράσουμε τις οντότητες ξεχωριστά αλλά και την σημασία τους
για κάθε τίτλο μέσα στον οποίο βρίσκονται.
Λόγο του όγκου του dataset θα προτιμήσουμε την αποφυγή όσο το δυνατόν περισσότερο της χειροκίνητη επισήμανσης (manual labeling) και θα προσπαθήσουμε
πρώτα να εξάγουμε keywords και key-phrases με απλές μεθόδους προκειμένου να μπορέσουμε να ταυτοποιήσουμε μαζικά την σημασία κάθε λέξης ή συνόλου λέξεων
για κάθε τίτλο προϊόντος.
Μία λέξη μπορεί να υπάρχει σε τίτλους προϊόντων που ανήκουν σε διαφορετικές κατηγορίες και να έχει την ίδια έννοια αλλά προφανώς να έχει διφορετικό ρόλο,
αυτό θα πρέπει να κρίνουμε ποιός είναι ο κατάλληλος τρόπος να το εκφράσουμε.

Για την χαρτογράφιση του dataset μας από την βάση δεδομένων και την εξαγωγή ενός r2rml mapping θα χρησιμοποιήσουμε το Protege με το plugin Ontop

Για την μεταφορά των δεδομένων από τη mysql βάση στο virtuoso db θα χρησιμοποιήσουμε δικό μας κώδικα σε python με την βιβλιοθήκη rdflib.

μετά το βήμα 5_2 εκτελούμε το παρακάτω query για να δούμε τις αντιστοιχίες κατηγοριών που δώσαμε

και μέσω αυτού του query μπορούμε να δούμε ποιά χαρακτιριστικά ανοίκουν σε κάθε κατηγορία

SELECT DISTINCT ?attribute ?has_attribute 
where{
?attribute a <http://magelon.com/ontologies/attributes>.
?product a <http://magelon.com/ontologies/products>;
           <http://magelon.com/ontologies/products#google_product_type> <http://magelon.com/ontologies/google_categories/id=267>;
           ?has_attribute ?attribute.
}

και κατ' επέκταση με το παρακάτω να δουμέ ποιά προϊόντα έχουν κοινά χαρακτηριστικά με μια κατηγορία αλλά δεν έχουν κατηγορία από μόνα τους


SELECT ?product ?title
where{
?product a <http://magelon.com/ontologies/products>;
                  <http://magelon.com/ontologies/products#title> ?title;
                  ?has_attribute ?attribute.
FILTER NOT EXISTS{?product <http://magelon.com/ontologies/products#google_product_type> ?google_product_type}
{
?attribute a <http://magelon.com/ontologies/attributes>.
?p a <http://magelon.com/ontologies/products>;
           <http://magelon.com/ontologies/products#google_product_type> <http://magelon.com/ontologies/google_categories/id=267>;
           ?has_attribute ?attribute.
}
}GROUP by ?product ?title