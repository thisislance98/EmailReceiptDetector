import random
import re


def remove_regex(array_of_strings, regex):
    """
    helper function for removing regexes
    :param array_of_strings: array of strings to clean
    :param regex: regex pattern to remove
    :return: array containing dictionary of clean strings and removal locations
    """
    out_array = []
    for text in array_of_strings:
        # match_locs = []
        # for item in re.finditer(regex, text):
        #    match_locs.append(list(item.span()))
        clean_text = regex.sub(" ", text)
        # out_array.append({"clean_string": clean_text, "array_of_locs": match_locs})
        out_array.append(clean_text)
    return out_array


def remove_special_characters(array_of_strings):
    # maybe use regex ?
    """
    remove punctuation/special characters, not including currency symbols
    :param array_of_strings: array of strings to be cleaned
    :return: array of clean strings
    """
    out_array = []
    remove_table = str.maketrans('', '', '\"%[]{}+()-*&^~=!;:|\\')
    for text in array_of_strings:
        out_array.append(text.translate(remove_table))
    return out_array


def remove_new_line_space(array_of_strings):
    """
    remove \n and nbsp&
    :param array_of_strings: array of strings to be cleaned
    :return: array containing dictionary of clean strings and removal locations
    """
    match = re.compile(r'\r\n|\r|\n|\t|&nbsp;')

    return remove_regex(array_of_strings, match)


def remove_hex_colors(array_of_strings):
    """
    remove hex codes
    :param array_of_strings: array of strings to be cleaned
    :return: array containing dictionary of clean strings and removal locations
    """
    match = re.compile(r'#(?:[0-9a-fA-F]{1,2}){3}')

    return remove_regex(array_of_strings, match)


def remove_pixels(array_of_strings):
    """
    remove 100px
    :param array_of_strings: array of strings to be cleaned
    :return: array containing dictionary of clean strings and removal locations
    """
    match = re.compile(r'\b\d*px\b', flags=re.IGNORECASE)

    return remove_regex(array_of_strings, match)


def remove_urls(array_of_strings):
    """

    :param array_of_strings:
    :return:
    """
    match = re.compile(r'(?:(?:https?|ftp):\/\/|\b(?:[a-z\d]+\.))(?:(?:[^\s()<>]+|\((?:[^\s()<>]+|'
                       r'(?:\([^\s()<>]+\)))?\))+(?:\((?:[^\s()<>]+|(?:\(?:[^\s()<>]+\)))?\)'
                       r'|[^\s`!()\[\]{};:‘“.,<>?«»“”‘’]))?', flags=re.IGNORECASE)

    return remove_regex(array_of_strings, match)


def remove_fonts(array_of_strings):
    # TODO get a list of fonts
    pass


def spin_cycle(array_of_strings):
    # just for fun
    spin_text = []
    for text in array_of_strings:
        spin_text.append(''.join(random.sample(text, len(text))))

    return spin_text


def remove_html_words(array_of_strings):
    # TODO maybe use spacy stopwords
    """
    remove html commonly found in emails
    :param array_of_strings: array of strings to be cleaned
    :return: array containing dictionary of clean strings and removal locations
    """
    with open('html_words.txt') as f:
        remove_words = f.read().splitlines()
    print(remove_words)
    remove = '\\b|\\b'.join(remove_words)
    match = re.compile(r'(' + remove + ')', flags=re.IGNORECASE)

    return remove_regex(array_of_strings, match)
