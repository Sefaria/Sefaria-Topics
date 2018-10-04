#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gensim as gen
import codecs

from Constants import ALL_CLEAN_DOCS_FILENAME, DOC2VEC_MODEL


class SegmentGenerator(object):
    def __init__(self, segments_filename):
        self.segments_filename = segments_filename

    def __iter__(self):
        with codecs.open(self.segments_filename, 'rb', encoding='utf8') as the_file:
            for line in the_file:
                ref = line.split(u"||||")[0]
                data = line.split(u"||||")[1]
                yield gen.models.doc2vec.TaggedDocument(gen.utils.simple_preprocess(data), [ref])


print("Creating Segment Generator...")
segments_generator = SegmentGenerator(ALL_CLEAN_DOCS_FILENAME)
print("Creating Doc2Vec model...")
model = gen.models.doc2vec.Doc2Vec(vector_size=100, min_count=2, epochs=40, dm=0, dbow_words=1)
print("Building Vocab...")
model.build_vocab(segments_generator)
print("Training Model...")
model.train(segments_generator, total_examples=model.corpus_count, epochs=10)

print("Saving Model...")
model.save(DOC2VEC_MODEL)
