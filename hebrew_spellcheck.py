# coding: utf-8

import codecs
import json
import re

dictionary_for_suffixes = {
    u"כינוי": {
        u"אני": u"אותי",
        u"אתה": u"אותך",
        u"את": u"אותך",
        u"הוא": u"אותו",
        u"היא": u"אותה",
        u"אנו": u"אותנו",
        u"אנחנו": u"אותנו",
        u"אתם": u"אתכם",
        u"אתן": u"אתכן",
        u"הם": u"אותם",
        u"הן": u"אותן",
    },
    u"של": {
        u"אני": u"שלי",
        u"אתה": u"שלך",
        u"את": u"שלך",
        u"הוא": u"שלו",
        u"היא": u"שלה",
        u"אנו": u"שלנו",
        u"אנחנו": u"שלנו",
        u"אתם": u"שלכם",
        u"אתן": u"שלכן",
        u"הם": u"שלהם",
        u"הן": u"שלהן",
    },
    u"סמיכות": u"של"
}


def we_havent_added_prefix_or_suffix(word):
    """
    Receives a modified word.  This word should have been expanded into prefix - root - suffix.
    If the modified word only has one word, that means there has been no modification.
    :param word: The modified word
    :return: Boolean Value determining if the word has not been modified
    """
    return len(word.split()) == 1


def determine_beginning_stopword(beginning_stopword):
    """
    Appends the approproate beginning stopword.  There are three possibilites,
    therefore the correct option needs to be determine
    :param beginning_stopword: The modified word
    :return: Appropriate beginning stopword
    """
    word = beginning_stopword.group(1).strip(',')
    if word == u"הווה,רבים":
        return u"אנחנו"
    elif word == u"הווה,יחיד":
        return u"אני"
    else:
        return word


def get_stopword_at_beginning(conj):
    """
    Get the beginning stopword
    :param conj: conjugation information of word
    :return: Stopword if known, otherwise None
    """
    pronouns = '|'.join([u"אני", u"אתה", u"את", u"הוא", u"היא", u"אנו", u"אתם", u"אתן", u"הם", u"הן"])
    stopword_beginning_pattern = re.compile(ur"(,({})(,|$)|(הווה,רבים|הווה,יחיד))".format(pronouns))
    return stopword_beginning_pattern.search(conj.strip())


def get_stopword_at_end(conj):
    """
    Get the end stopword
    :param conj: conjugation information of word
    :return: Stopword if known, otherwise None
    """
    last_word = conj.split(',')[-1].strip()
    if last_word == u"סמיכות":
        return dictionary_for_suffixes[last_word]
    elif u'/' in last_word:
        shel_or_kinui = last_word.split(u'/')[0]
        pronoun = last_word.split(u'/')[1]
        return dictionary_for_suffixes[shel_or_kinui][pronoun]
    else:
        return None


def create_each_replacement(one_possible_conjugation):
    """
    Replaces a word with its prefix-root-suffix
    :param one_possible_conjugation: dict of a word and its meta-information
    :return: prefix-root-suffix replacement
    """
    full_replacement = {'root': one_possible_conjugation['root'].strip()}
    conj = one_possible_conjugation['conjugation']

    beginning_stopword = get_stopword_at_beginning(conj)
    if beginning_stopword:
        full_replacement['prefix'] = determine_beginning_stopword(beginning_stopword)

    end_stopword = get_stopword_at_end(conj)
    if end_stopword:
        full_replacement['suffix'] = end_stopword

    return full_replacement


def choose_one_replacement(replacements):
    """
    Takes a list of possible replacements.  Each replacement is the expansion of a word into its prefix-root-suffix.
    Replacement is returned only when there is no ambiguity  However, if there is any level of ambiguity, None is returned.
    This methods tries to find the least common denominator of agreement.  If all replacement options agree on the suffix but there is ambiguity in the prefix, the root-suffix is returned.
    :param replacements: List of possible replacements to be selected
    :return: Selected Replacement without Ambiguity.  In case of ambiguity, None is returned
    """

    if any(len(d) == 1 for d in replacements):
        return None

    if len(replacements) == 1:
        d = replacements.pop()
        full_replacement = u"{} {} {}".format(d.get('prefix', u''), d.get('root', u''), d.get('suffix', u''))
        return full_replacement.strip()

    shoreshim = set([x['root'] for x in replacements])
    if len(shoreshim) > 1:
        return None

    full_replacement = shoreshim.pop()
    if all('prefix' in d for d in replacements):
        full_replacement = u"{} {}".format(replacements[0]['prefix'], full_replacement)
    if all('suffix' in d for d in replacements):
        full_replacement = u"{} {}".format(full_replacement, replacements[0]['suffix'])

    if we_havent_added_prefix_or_suffix(full_replacement):
        return None

    return full_replacement


def read_in_json_file(filename):
    """
    Return the entire content of a json file
    :param filename: Name of file to return
    :return: Dict which is the entire JSON file
    """
    with codecs.open(filename, encoding='utf8') as hspell:
        whole_file = json.load(hspell)
    return whole_file


def split_word_into_root_and_suffix():
    whole_file = read_in_json_file('./all_hebrew_inv.json')
    word_expander = {}
    for full_word, all_conjugations in whole_file.items():
        replacements = [create_each_replacement(each_conj) for each_conj in all_conjugations]
        replacement = choose_one_replacement(replacements)
        if replacement:
            word_expander[full_word] = replacement
    return word_expander


word_expander = split_word_into_root_and_suffix()


