#!/usr/bin/env python
# -*- coding: utf-8 -*-


TEST_TOPICS = [u"פסח", u"תפילה", u"משה", u"אברהם", u"צדקה", u"שבת", u"רות", u"אסתר", u"תשובה", u"חטא", u"חגים",
               u"קהילה", u"ישראל", u"צדק", u"התגלות", u"אהבה", u"מין", u"תפילין", u"סביבה",
               u"אב_מלאכה", u"בית_שני", u"אבן_שתיה", u"אדר_שני", u"גמילות_חסדים", u"גיד_נשה",
               u"גזירה_שוה", u"גוג_מגוג", u"חייב_שבועה", u"כהן_משיח", u"ליל_פסח",
               u"מעשה_עגל", u"עשרה_מאמרות", u"שבעים_לשון", u"תרומת_דשן"]

HEBREW_WIKI = False

DOC2VEC_MODEL = "doc2vec.model" if HEBREW_WIKI else "doc2vec_wo_wiki.model"
ALL_CLEAN_DOCS_FILENAME = 'cleaned_docs_for_doc2vec.txt'
DICTA_HEBREW_WIKI_FILENAME = './Hebrew_Wiki_Dicta.txt'
DICTA_SEFARIA_FILENAME = './sefaria-export_prefix_refs.txt'