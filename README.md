# Sefaria Topics

Sefaria Topics aims to leverage Artificial Intelligence to find semantical connections between various topics through our entire corpus of text!

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

You will need three files to run this project
1. sefaria-export_prefix_refs.txt
2. cleaned_docs_for_doc2vec.txt
3. Hebrew_Wiki_Dicta.txt

### How to Run the Project

There are a total of three files that need to be run, in a particular order, to produce and test the doc2vec model

1. create_docs_for_doc2vec.py
    * Combs through the entire Sefaria Corpus to clean, preprocess and prepare the text to be trained in a Doc2Vec model.  Stopwords, punctuation and other trivial information need be removed as well as Docs need to be defined.  Additionally, multiple word phrases are also dealt with in this file.  Lastly, there is the option to include Hebrew Wikipedia into the corpus as well (boolean is set in the Constants file) 
2. Doc2Vec.py
    * Trains a Doc2Vec Model using the Docs created in the previous file
3. Doc2Vec_test_model.py
    * Tests the model on a predefined list of key topics.

## Authors

* **Noah Santacruz** - *Project Manager / Chief Data Scientist*
* **Joshua Goldmeier** - *Data Scientist*


## License

[GNU](https://www.gnu.org/copyleft/gpl.html)
