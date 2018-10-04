
# coding: utf-8

# In[1]:


#!/usr/bin/env python
# -*- coding: utf-8 -*-


# In[236]:


import warnings; warnings.simplefilter('ignore')
import gensim as gen
import json
import codecs
import bleach
import re
from optparse import OptionParser

parser = OptionParser()
parser.add_option("-f", "--file", dest="file", action="store", type="string")
(options, args) = parser.parse_args()

dicta_prefixes = options.file


import local_settings
import django
django.setup()

from sefaria.model import *


# In[39]:


def get_rid_of_stopwords(data):
    data = remove_dicta_prefix(data)
    data = data.split()
    return ' '.join([word for word in data if word not in stopwords])

def remove_dicta_prefix(data):
    data = re.sub(ur'[\u05d0-\u05ea]+┉', u'', data)
    return data

def remove_punctuation(data):
    data = re.sub(ur'־', u' ', data)
    data = re.sub(ur'\([^)]+\)', u'', data)
    data = re.sub(ur'\[[^\]]+\]', u'', data)
    data = re.sub(ur'[^ \u05d0-\u05ea"\'״׳]', u'', data)
    data = re.sub(ur'\s["״]', u' ', data)
    data = re.sub(ur'["״]\s', u' ', data)
    return data

def clean_data(data):
    data = data.split('~~')[1]
    data = bleach.clean(data, tags=[], strip=True)
    data = remove_punctuation(data)
    return data

def read_in_chunks(file_object):
    """Lazy function (generator) to read a file line by line"""
    while True:
        data = file_object.readline().strip()
        if not data:
            break
        if '~~' not in data:
            continue
        data = get_rid_of_stopwords(data)
        data = clean_data(data)
        yield data


# In[40]:


f = open('./sefaria-export_prefix_refs.txt')
g = read_in_chunks(f)


# In[41]:


print(g.next())


# In[243]:


class SegmentGenerator(object):
    def __init__(self, filename, stopwords_filename, tokenizer=None):
        self.file = open(filename)
        self.stopwords = open(stopwords_filename).read().split('\n')
#         self.tokenizer = tokenize
        
    def get_rid_of_stopwords(self, data):
        data = self.remove_dicta_prefix(data)
        data = data.split()
        return ' '.join([word for word in data if word not in self.stopwords])

    def remove_dicta_prefix(self, data):
        data = re.sub(ur'[\u05d0-\u05ea]+┉', u'', data)
        return data

    def remove_punctuation(self, data):
        data = re.sub(ur'־', u' ', data)
        data = re.sub(ur'\([^)]+\)', u'', data)
        data = re.sub(ur'\[[^\]]+\]', u'', data)
        data = re.sub(ur'[^ \u05d0-\u05ea"\'״׳]', u'', data)
        data = re.sub(ur'\s["״]', u' ', data)
        data = re.sub(ur'["״]\s', u' ', data)
        return data

    def clean_data(self, data):
        data = data.split('~~')[1]
        data = bleach.clean(data, tags=[], strip=True)
        data = self.remove_punctuation(data)
        return data

    def __iter__(self):
#         yield 5
        for data in self.file:
#             data = open(self.filename).readline().strip()
            if not data:
                raise StopIteration
            if '~~' not in data:
                continue
            data = self.get_rid_of_stopwords(data)
            data = self.clean_data(data)
            yield data.split()
        


# Initiate a SegmentGenerator object to pass to the model

# In[244]:


dicta_prefix_file = './sefaria-export_prefix_refs.txt'  
stopwords_file = './hebrew_stopwords.txt'

segments = SegmentGenerator(dicta_prefixes, stopwords_file)


# In[235]:


print(next(segments.__iter__()))


# ### Model intiation

# In[245]:


model = gen.models.Word2Vec(size=100, window=5)


# Now we have initiated the Word2Vec model. The next step is to call the **build_vocab** method for the preliminary scan of the text. Call the method and print how many words are in the vocabulary of our text

# In[246]:


model.build_vocab(segments)
print("Number of words in vocabulary: {}".format(len(model.wv.vocab)))


# In the previous step we created the vocabulary for our model, it is now time to train! Don't forget to add the following parameters:
# 1. total_examples=model.corpus_count 
# 2. epochs=model.epochs

# In[248]:


segments = SegmentGenerator(dicta_prefix_file, stopwords_file)


# In[ ]:


model.train(segments, total_examples=model.corpus_count, epochs=10)


# Test a few words

# In[ ]:


WORD = ________




