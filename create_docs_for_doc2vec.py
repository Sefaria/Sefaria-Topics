#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import codecs
import regex as re
import os.path
import csv

import local_settings

import django

from Constants import ALL_CLEAN_DOCS_FILENAME, DICTA_HEBREW_WIKI_FILENAME, DICTA_SEFARIA_FILENAME, HEBREW_WIKI

django.setup()

from sefaria.model import *
from sefaria.system.exceptions import InputError, PartialRefInputError

import hebrew_spellcheck
word_expander = hebrew_spellcheck.word_expander

stopwords = codecs.open('./hebrew_stopwords.txt', encoding='utf8').read().strip().split('\n')
stopwords_regex = u"(?:\s|^)({})(?=\s|$)".format(u"|".join(stopwords))
stopwords_regex = re.compile(stopwords_regex)

phrases = codecs.open('./select_phrases.txt', encoding='utf8').read().strip().split('\n')
phrases_regex = u"(\s|^)({})(?=\s|$)".format(u"|".join(phrases))
phrases_regex = re.compile(phrases_regex)


def get_talmud_topic_ranged():
    """
    Reads every file in the sugyot directory.
    Each file in this directory contains semantically meaningful ranged refs for Talmud
    :return: List of all Talmudic Ranged Refs
    """
    all_gemara_topic_ranges = []
    for filename in os.listdir('./sugyot/'):
        with codecs.open('./sugyot/' + filename, 'rb', encoding='utf8') as csvfile:
            reader = csv.reader(csvfile)
            reader.next()
            all_gemara_topic_ranges += [row[0] for row in reader]
    return all_gemara_topic_ranges


def create_list_off_talmud_books():
    """
    Uses Sefaria Project to create a list of titles of every Talmud Tractate
    :return: Set of all Talmud book titles
    """
    indexes = library.all_index_records()
    talmud_books = set(library.get_indexes_in_category("Bavli"))
    talmud_books_modified = {u'Avodah Zarah', u'Bava Batra', u'Bava Kamma',
                             u'Bava Metzia', u'Beitzah', u'Berakhot', u'Chagigah', u'Eruvin', u'Gittin', u'Horayot',
                             u'Ketubot', u'Kiddushin', u'Makkot', u'Megillah', u'Menachot', u'Moed Katan',
                             u'Nazir', u'Nedarim', u'Pesachim', u'Rosh Hashanah', u'Sanhedrin', u'Shabbat', u'Shevuot',
                             u'Sotah', u'Sukkah', u'Taanit', u'Yevamot', u'Yoma', u'Zevachim'}
    return talmud_books_modified


def create_list_off_tanakh_books():
    """
    Uses Sefaria Project to create a list of titles of every book in Tanakh
    :return: Set of all Tanakh book titles
    """
    indexes = library.all_index_records()
    tanakh_books = set(library.get_indexes_in_category("Tanakh"))
    tanakh_books_modified = set([u'Judges', u'Deuteronomy', u'Genesis', u'Exodus',
                                 u'Leviticus', u'II Kings', u'Joshua',
                                 u'I Samuel', u'Numbers', u'I Kings', u'II Samuel'])
    return tanakh_books_modified


def get_tanakh_topic_ranges():
    """
    Creates semantically meaningful ranged refs for Tanakh using Herzog's breakdown
    :return: List of all Tanakh Ranged Refs
    """
    with codecs.open('level_3_wo_overlaps.json', 'r', encoding='utf8') as the_file:
        segs = json.load(the_file, encoding='utf8')
    tanakh_topic_ranged_refs = []

    for seg in segs:
        b_ref = seg['b_ref']
        e_ref = seg['e_ref']
        book = b_ref.rsplit(' ', 1)[0]
        b_chapter = b_ref.rsplit(' ', 1)[1].split(':')[0]
        b_verse = b_ref.rsplit(' ', 1)[1].split(':')[1]
        e_chapter = e_ref.rsplit(' ', 1)[1].split(':')[0]
        e_verse = e_ref.rsplit(' ', 1)[1].split(':')[1]

        verses = "{}:{}-{}".format(b_chapter, b_verse, e_verse) if b_chapter == e_chapter else "{}:{}-{}:{}".format(
            b_chapter, b_verse, e_chapter, e_verse)
        tanakh_topic_ranged_refs.append("{} {}".format(book, verses))

    return tanakh_topic_ranged_refs


def segment_range_dicts(topic_ranged_refs):
    """
    Creates two dictionaries.  These are mappings between ranged refs and segments refs.
    This receives a list of ranged refs.  It iterates over every ranged ref and creates a mapping between the ranged refs and the segment refs.
    :param topic_ranged_refs: list of ranged refs
    :return: tuple of dicts. The first is dict mapping ranged refs to all segment refs.  The second is a dict mapping each segment ref to its corresponding ranged ref.
    """
    ranged_to_segment = {}
    segment_to_ranged = {}

    for topic_ranged_ref in topic_ranged_refs:
        ranged_to_segment[topic_ranged_ref] = {}
        topic_seg_refs = Ref(topic_ranged_ref).range_list()
        for seg_ref in topic_seg_refs:
            ranged_to_segment[topic_ranged_ref][seg_ref.normal()] = ""
            segment_to_ranged[seg_ref.normal()] = topic_ranged_ref

    return ranged_to_segment, segment_to_ranged


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


def pull_out_suffix(string):
    """
    Receives a string of Hebrew Text.  Iterates over every hebrew word and splits each
    word into its root and suffix.
    :param string: String of Hebrew Text
    :return: String with Hebrew compound words split into Root and Suffix
    """
    string = string.split()
    string = ' '.join([word_expander.get(word, word) for word in string])
    return string


def remove_stopwords(string):
    """
    Replaces Stopwords with a space character
    :param string: String of Hebrew Text
    :return: String without stopwords
    """
    return re.sub(stopwords_regex, u' ', string)


def remove_dicta_prefix(string, marker):
    """
    Removes prefixes that were detected by Dicta
    :param string: String of Hebrew Text
    :return: String without prefixes
    """
    return re.sub(ur'[\u05d0-\u05ea]+{}'.format(marker), u'', string)
    # return re.sub(ur'[\u05d0-\u05ea]+┉', u'', string)


def remove_punctuation(data):
    """
    Removes various punctuation from Hebrew text.
    :param data: String of Hebrew Text
    :return: String without punctuation
    """
    data = re.sub(ur'־', u' ', data)
    data = re.sub(ur'\([^)]+\)', u' ', data)
    data = re.sub(ur'<[^>]+>', u' ', data)
    data = re.sub(ur'\[[^\]]+\]', u' ', data)
    data = re.sub(ur'[^ \u05d0-\u05ea"\'״׳]', u' ', data)
    data = re.sub(ur'(^|\s)["\'״׳]+', u' ', data)
    data = re.sub(ur'["\'״׳]+(\s|$)', u' ', data)
    return data


def strip_stopwords_and_remove_punctuation(data):
    """
    This method takes a string of hebrew text and does all necessary cleaning for Word2Vec.
    :param data: String of Hebrew Text
    :return: String ready for Word2Vec model
    """
    data = data.strip().split(u'~~')[1]
    data = remove_dicta_prefix(data, u"┉")
    data = remove_punctuation(data)
    data = pull_out_suffix(data)
    data = remove_stopwords(data)
    data = u' '.join(data.split())
    return data


def create_multiple_word_phrases(data):
    """
    Combines selected multiple word phrases with underscore.
    For example:  New York ----> New_York
    This allows Word2Vec to handle multiple word phrases
    :param data: String of Hebrew Text
    :return: String with connected multiple word phrases
    """

    def connect_with_underscore(matchobj):
        return matchobj.group(1) + matchobj.group(2).replace(u" ", u"_")

    return re.sub(phrases_regex, connect_with_underscore, data)


def this_is_a_bad_line(data):
    """
    Checks to see if a line from the file should be included in the Word2Vec model.
    There are some lines within the Dicta Prefix file that we cannot or do not want to include.
    :param data: line of hebrew text from Dicta File
    :return: Boolean Value determining if this line valid
    """
    if u'~~' not in data:
        return True
    if data.strip().split(u'~~')[1].strip().startswith(u"<br><br><big><strong>הדרן עלך"):
        return True

    return False


def extract_reference(data):
    """
    Extract Sefaria Ref from a line in the Dicta Prefix file
    :param data: A line from the dicta file
    :return: The Corresponding tref
    """
    return data.split(u'~')[0]


def concatenate_semantically_linked_segments(topic_ranged_refs, ranged_to_segment):
    """
    Combines multiple Sefaria Segments into one larger segment based on semantical meaning
    :param topic_ranged_refs: List of ranged trefs that define the semantic separation
    :param ranged_to_segment: Nested dict.  First layer points from Ranged Refs to all sub-seg-refs.  The nested dict points from the sub_seg_ref to the text of said sub_seg_ref
    :return: Dict containing semantically define ranged refs corresponding to their concatenated text
    """
    semantic_linked_segments = {}
    for text_ranged_ref in topic_ranged_refs:
        object_ref = Ref(text_ranged_ref)
        all_text_subrefs = [seg_ref.normal() for seg_ref in object_ref.range_list()]
        all_verses = [ranged_to_segment[text_ranged_ref][seg_ref] for seg_ref in all_text_subrefs]
        semantic_linked_segments[text_ranged_ref] = u' '.join(all_verses)
    return semantic_linked_segments


def get_segments(filename):
    """
    Combs through the entire Sefarias Hebrew Library and cleans the text for Doc2Vec.
    Creates a dict:
        Key:  Ref
        Value:  The text of that ref cleaned and ready for Doc2Vec
    :param filename: Dicta Prefix Filename
    :return: Dict for Doc2Vec
    """

    all_tanakh_books = create_list_off_tanakh_books()
    all_talmud_books = create_list_off_talmud_books()

    tanakh_topic_ranged_refs = get_tanakh_topic_ranges()
    talmud_topic_ranged_refs = get_talmud_topic_ranged()

    tanakh_ranged_to_segment, tanakh_segment_to_ranged = segment_range_dicts(tanakh_topic_ranged_refs)
    talmud_ranged_to_segment, talmud_segment_to_ranged = segment_range_dicts(talmud_topic_ranged_refs)

    all_data = {}

    for index, data in enumerate(codecs.open(filename, encoding='utf8')):

        if this_is_a_bad_line(data):
            continue

        ref = extract_reference(data)
        data = strip_stopwords_and_remove_punctuation(data)
        data = create_multiple_word_phrases(data)

        if index % 100000 == 0:
            print index

        if is_from_category(ref, all_tanakh_books):
            this_ref_ranged_reg = tanakh_segment_to_ranged[ref]
            tanakh_ranged_to_segment[this_ref_ranged_reg][ref] = data
        elif is_from_category(ref, all_talmud_books):
            this_ref_ranged_reg = talmud_segment_to_ranged[ref]
            talmud_ranged_to_segment[this_ref_ranged_reg][ref] = data
        else:
            all_data[ref] = data

    all_data.update(concatenate_semantically_linked_segments(tanakh_topic_ranged_refs, tanakh_ranged_to_segment))
    all_data.update(concatenate_semantically_linked_segments(talmud_topic_ranged_refs, talmud_ranged_to_segment))

    return all_data


def get_wiki_segs(filename):
    all_data = {}
    for index, data in enumerate(codecs.open(filename, encoding='utf8')):
        ref = u"Random {}".format(index)
        data = remove_dicta_prefix(data, u"\|")
        data = remove_punctuation(data)
        data = pull_out_suffix(data)
        data = remove_stopwords(data)
        data = u' '.join(data.split())
        data = create_multiple_word_phrases(data)
        if index % 100000 == 0:
            print index
        all_data[ref] = data
    return all_data


if __name__ == "__main__":
    segments = get_segments(DICTA_SEFARIA_FILENAME)
    if HEBREW_WIKI:
        wiki_segs = get_wiki_segs(DICTA_HEBREW_WIKI_FILENAME)

    with codecs.open(ALL_CLEAN_DOCS_FILENAME, 'wb', encoding='utf8') as the_file:
        for k, v in segments.items():
            the_file.write(u""+k+u"||||"+v+u"\n")
        if HEBREW_WIKI:
            for k, v in wiki_segs.items():
                the_file.write(u""+k+u"||||"+v+u"\n")