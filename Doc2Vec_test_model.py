#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import json
from gensim.models import Doc2Vec
from collections import Counter
from scipy import spatial

from Constants import TEST_TOPICS, DOC2VEC_MODEL
from create_docs_for_doc2vec import get_tanakh_topic_ranges, get_talmud_topic_ranged, segment_range_dicts, \
    create_list_off_talmud_books, create_list_off_tanakh_books

import local_settings
import django

django.setup()

from sefaria.model import *
from sefaria.system.exceptions import InputError, PartialRefInputError


def get_ref_score(topic, ref, model):
    """
    Calculated the Cosine Similarity between a word vector and a doc vector
    :param ref: A ref of a particular doc in Doc2Vec
    :param model: The Doc2Vec Model
    :return: Cosine Similarity
    """
    score = 0
    try:
        score = 1-spatial.distance.cosine(model.docvecs[ref], model[topic])
    except KeyError:
        pass
    return score


def convert_to_range(tref):
    """
    Finds the corresponding ranged Ref for a segment Ref
    :param tref: Ref
    :return: Ranged Ref
    """
    return segment_to_ranged[tref]


def convert_select_segs_to_ranged_refs(references):
    """
    There are unique ranged Refs for particular books based on semantical divisions
    Replaces segment refs with a the ranged Ref that it belongs to
    :param references: set of Refs
    :return: set Of Refs with particular segment refs replaced by their ranged Ref
    """
    updated_set = set()
    for tref in references:
        if is_from_category(tref, tanakh_and_talmud):
            updated_set.add(convert_to_range(tref))
        else:
            updated_set.add(tref)
    return updated_set


def expand_all_ranged_refs(sources_to_add):
    """
    Iterates over a list of Refs and expands all ranged refs into all of their segment refs
    :param sources_to_add: list of Refs
    :return: List of segment level Refs with no range Refs
    """
    new_list = []
    for tref in sources_to_add:
        oref = Ref(tref)
        if oref.is_range():
            new_list += [x.normal() for x in oref.range_list()]
        else:
            new_list.append(tref)
    return new_list


def more_than_n_occurrence(all_sources, n):
    """
    Returns all elements of a list that appear more than n times
    :param all_sources: list of anything
    :param n: minimum number of occurrences
    :return: list with elements that appear more than n times
    """
    x = Counter(all_sources)
    sources_with_more_than_n_instances = [k for k, v in x.items() if v >= n]
    return sources_with_more_than_n_instances


def ref_is_not_ranged(tref):
    """
    Checks if a Ref is a segment level Ref
    :param tref: Ref
    :return: Boolean Value indicating if the Ref is segment level
    """
    try:
        return not Ref(tref).is_range()
    except InputError:
        return False


def ref_is_segment_level(tref):
    """
    Checks if a Ref is a segment level Ref
    :param tref: Ref
    :return: Boolean Value indicating if the Ref is segment level
    """
    try:
        return Ref(tref).is_segment_level()
    except InputError:
        return False


def all_refs_linked_to_this_ref(tref, segment_level=False):
    """
    Finds every Ref linked to a particular Ref
    :param tref: Selected Ref
    :param segment_level: If True, will only include segment level Refs
    :return: List of all Refs linked to selected Ref
    """
    oref = Ref(tref)
    all_refs = [x for l in oref.linkset() for x in l.refs if x != tref]
    if segment_level:
        all_refs = [x for x in all_refs if ref_is_segment_level(x)]
    return all_refs


def get_closest_related_sources(model, topic, threshold):
    """
    Returns a list of closest DocIDs to a particularly word or doc based on the Cosine Similarity.
    Doc2Vec only allows you to select the topn amount however this method allows one
    to select all sources that are above a certain cosine similarity threshold
    :param model: Doc2Vec Model
    :param topic: Doc or Word you want to Query
    :param threshold: Cosine Similarity Threshold
    :return: A list of sources that are above the Cosine Similarity Threshold
    """
    print topic
    topn = 1000
    x = 1
    while x > threshold:
        topic_sources = model.docvecs.most_similar([model[topic]], topn=topn)
        x = topic_sources[-1][1]
        topn *= 2
    sources_above_threshold = [x[0] for x in topic_sources if x[1] > threshold]
    sources_above_threshold = [x for x in sources_above_threshold if Ref.is_ref(x)]
    return sources_above_threshold


def add_popular_links(related_sources):
    """
    Expands a list of Refs to include all Refs that are one degree of separation from any of the Refs in the original list.
    In other words, this expanded list of Refs will include the original set of Refs along with any Ref that is linked to those original Refs
    :param related_sources: List of Refs
    :return: Expanded list of Refs
    """
    set_of_related = set(related_sources)
    sources_to_add = []
    for tref in related_sources:
        try:
            sources_to_add += all_refs_linked_to_this_ref(tref, segment_level=True)
        except PartialRefInputError:
            continue
    sources_to_add = expand_all_ranged_refs(sources_to_add)
    popular_links = more_than_n_occurrence(sources_to_add, n=5)
    popular_links = convert_select_segs_to_ranged_refs(popular_links)
    set_of_related.update(popular_links)
    return set_of_related


def page_rank_score(topic, set_of_related, model):
    """
    Gensim's most_similar returns a list of most similar order by Cosine Similarity.  This Methods aims to use a
    pagerank style approach to re-order selected sources in a more fitting way for Sefaria.
    The sources that have more incoming links will be have more Value
    :param set_of_related: List of sources to be re-ordered
    :param model: Doc2Vec Model
    :return: Sources with updated scores
    """
    scores_of_related_sources = {}
    for tref in set_of_related:
        if not ref_is_segment_level(tref):
            continue
        scores_of_related_sources[tref] = get_ref_score(topic, tref, model)
        all_refs = all_refs_linked_to_this_ref(tref, segment_level=True)
        scores_of_related_sources[tref] += sum([get_ref_score(topic, x, model) for x in all_refs if x in set_of_related])
    return scores_of_related_sources


def evaluate_model_topics(model, test_topics):
    """
    Evaluates a Doc2Vec Model's ability to predict related sources given a variety of different topics
    :param model: Doc2Vec Model
    :param test_topics: List of Topics to test the model
    :return: Dict with a list of predicted sources for each test topic
    """
    topics_and_related_sources = {}
    for topic in test_topics:
        related_sources = get_closest_related_sources(model, topic, threshold=0.6)
        related_sources = add_popular_links(related_sources)
        final_scores = page_rank_score(topic, related_sources, model)
        final_scores = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)
        topics_and_related_sources[topic] = final_scores[:100]
    return topics_and_related_sources


def is_from_category(ref, books_in_category):
    """
    Checks to see if a tref belongs to a list of book within a particular category
    For Example:  Is Genesis 12:3 within Tanakh
    :param ref: tref to be examined
    :param books_in_category: List of books in category
    :return: Boolean Value determining if Tref is within category
    """
    try:
        if Ref(ref).index.title in books_in_category:
            return True
        else:
            return False
    except InputError:
        return False


def evaluate_model_words(model, test_topics):
    results = {}
    for topic in test_topics:
        print topic
        similar_words = model.most_similar([model[topic]], topn=20)
        similar_words = sorted(similar_words, key=lambda tup: tup[1], reverse=True)
        results[topic] = similar_words
    return results


def save_dict_in_json(obj, filename):
    with codecs.open(filename, 'w', encoding='utf8') as the_file:
        json.dump(obj, the_file, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    tanakh_topic_ranged_refs = get_tanakh_topic_ranges()
    talmud_topic_ranged_refs = get_talmud_topic_ranged()

    _, segment_to_ranged = segment_range_dicts(tanakh_topic_ranged_refs + talmud_topic_ranged_refs)

    tanakh_and_talmud = create_list_off_tanakh_books() | create_list_off_talmud_books()

    model = Doc2Vec.load(DOC2VEC_MODEL)

    topics_with_related_words = evaluate_model_words(model, TEST_TOPICS)
    topics_with_related_sources = evaluate_model_topics(model, TEST_TOPICS)

    save_dict_in_json(topics_with_related_words, 'test_words.json')
    save_dict_in_json(topics_with_related_sources, 'test_topics.json')
