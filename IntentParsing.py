from typing import List, Optional

import nltk
from nltk.corpus import wordnet as wn
from nltk.tokenize import sent_tokenize
from google.cloud import dialogflow_v2beta1 as df
import locationtagger
import warnings
import operator


def get_raw_kb_text(doc_name: str) -> str:
    """
    Gets the raw bytes from the document in the knowledgebase
    Args: str
        doc_name: Name of the document to pull from
    Returns: List[str]
      the words that matched sysnets
    """
    client = df.DocumentsClient()
    return str(client.get_document(name=doc_name))


def get_most_frequent_words_in_synsets(
        text: str, synsets: List[str],
        max_num_to_return: int,
        min_threshold: Optional[float] = 0.0,
        banned_words: Optional[List[str]] = []
) -> List[str]:
    """
    Use TF to get the most frequent words that match a sysnet in the list of sysnets
    Args: str, List[str], int, List[str]
        text: the text to be analyzed
        sysnets: the sysnets the text will be compared against
        max_num_to_return: the maximum number of words to return
        min_threshold: the minimum relative frequency percentage for when you should include a word
        banned_words: to words not to include in the results
    Returns: List[str]
      the words that matched sysnets
    """
    warnings.filterwarnings('ignore')
    total_count = 0

    word_counts = {}
    for word in text.split():
        word = word.lower()
        if word not in banned_words:
            hyper = lambda s: s.hypernyms()
            word_synsets = wn.synsets(word)
            if len(word_synsets) > 0:
                hypernyms = list(word_synsets[0].closure(hyper))
                for synset in synsets:
                    if synset in hypernyms:
                        total_count += 1
                        if word in word_counts:
                            word_counts[word] += 1
                        # check if singular form of word is already counted
                        elif len(word) > 1 and word[:len(word) - 1] in word_counts:
                            word_counts[word[:len(word) - 1]] += 1
                        # check if plural form of word is already counted
                        elif word + 's' in word_counts:
                            word_counts[word + 's'] += 1
                        else:
                            word_counts[word] = 1
    sorted_words = sorted(word_counts.items(), key=operator.itemgetter(1), reverse=True)

    result = []
    x = 0
    while x < len(sorted_words):
        if min_threshold is not None:
            if sorted_words[x][1] / total_count < min_threshold:
                x += 1
                continue
        result.append(sorted_words[x][0])
        x += 1
        if x == max_num_to_return:
            return result
    return result


def get_words_in_synsets(text: str, synsets: List[str]) -> List[str]:
    warnings.filterwarnings('ignore')
    words = []
    for word in text.split():
        word = word.lower()
        hyper = lambda s: s.hypernyms()
        word_synsets = wn.synsets(word)
        if len(word_synsets) > 0:
            hypernyms = list(word_synsets[0].closure(hyper))
            for synset in synsets:
                if synset in hypernyms:
                    if word not in words:
                        words.append(word)
    return words


def create_word_list_string(words) -> str:
    if len(words) == 1:
        return words[0]
    elif len(words) == 2:
        return words[0] + ' and ' + words[1]
    elif len(words) > 0:
        response = ''
        for x in range(len(words)):
            if x == len(words) - 1:
                response += 'and ' + words[x]
            else:
                response += words[x] + ', '
        return response
    else:
        return ''


def get_words_in_synsets(text: str, synsets: List[str]) -> List[str]:
    """
    Analyzes a piece of text and returns words that match a sysnet from a provided list
    Args: str, List[str]
        text: the text to be analyzed
        sysnets: the sysnets the text will be compaerd against
    Returns: List[str]
      the words that matched sysnets
    """
    warnings.filterwarnings('ignore')
    words = []
    for word in text.split():
        word = word.lower()
        hyper = lambda s: s.hypernyms()
        word_synsets = wn.synsets(word)
        if len(word_synsets) > 0:
            hypernyms = list(word_synsets[0].closure(hyper))
            for synset in synsets:
                if synset in hypernyms:
                    if word not in words:
                        words.append(word)
    return words


def create_word_list_string(words: List[str]) -> str:
    """
    Separates words by commas and adds 'and' before the final word
    Args: List[str]
        words: the list of words to be joined
    Returns: str
      the list as a comma seperated string
    """
    if len(words) == 1:
        return words[0]
    elif len(words) == 2:
        return words[0] + ' and ' + words[1]
    elif len(words) > 0:
        response = ''
        for x in range(len(words)):
            if x == len(words) - 1:
                response += 'and ' + words[x]
            else:
                response += words[x] + ', '
        return response
    else:
        return ''

def get_proper_nouns(text: str, banned_words: [str], max: int) -> [str]:
    """
    Given a body of text, attempts to identify all proper noun phrases
    Args:
        text: the body of text to be processed
        banned_words: any words that should not be returned in the result list
        max: the maximum number of phrases to return
    Returns: [str]
      a list of proper noun phrases
    """
    pos_tags = nltk.pos_tag(nltk.word_tokenize(text))
    result = []
    x = 0
    while x < len(pos_tags):
        # identifying the start of a new proper noun phrase
        if pos_tags[x][1] == 'NNP':
            proper_noun = pos_tags[x][0]

            # check if the proper noun starts with 'the'
            if x > 0:
                if pos_tags[x-1][1] == 'DT':
                    proper_noun = pos_tags[x-1][0] + ' ' + proper_noun
            x+=1

            # check if the next word is also a proper noun or a connector
            while x < len(pos_tags) and (pos_tags[x][1] == 'NNP' or pos_tags[x][1] == 'IN'):
                # only consider a connecting word if it is followed by another proper noun
                if pos_tags[x][1] == 'IN':
                    if x < len(pos_tags)-1 and pos_tags[x+1][1] == 'NNP':
                        proper_noun += ' ' + pos_tags[x][0]
                else:
                    proper_noun += ' ' + pos_tags[x][0]
                x+=1

            # checks to ensure the phrases returned are substantial
            if proper_noun.replace(" ", "").isalpha() and \
                    proper_noun not in result and \
                    proper_noun not in banned_words and \
                    len(proper_noun) > 5 and \
                    len(proper_noun.split()) > 2:
                result.append(proper_noun)
                if len(result) == max:
                    return result
        else:
            x+=1
    return result

def form_understand_intent_response(kb_response: str, country_name: str, dislikes: List[str]) -> str:
    """
    Formats the response for the "understand" intent
        Args: str
            kb_response: the response from dialog flow
            dislikes: list of forbidden words to suggest
        Returns: str
      a sentence in the kb response
    """
    sents = sent_tokenize(kb_response)
    for sentence in sents:
        if any(dislike in sentence for dislike in dislikes):
            continue
        else:
            return sentence


def form_cities_intent_response(kb_response: str, country_name: str, dislikes: List[str]) -> str:
    """
    Formats the response for the "cities" intent
        Args: str, str, List[str]
            kb_response: the response from dialog flow
            country_name: the current country
            dislikes: list of forbidden words to suggest
        Returns: str
      a response to give to the user (either client created or dialogflow created)
    """
    locations = locationtagger.find_locations(text=kb_response)
    city_words = locations.cities
    if len(city_words) > 0:
        return "I recommend you don't miss " + create_word_list_string(
            [city for city in city_words[:3] if not any(dislike in city.lower() for dislike in dislikes)]) + '.'
    sents = sent_tokenize(kb_response)
    for sentence in sents:
        if any(dislike in sentence for dislike in dislikes):
            continue
        else:
            return sentence


def form_regions_intent_response(kb_response: str, country_name: str, dislikes: List[str]) -> str:
    """
    Formats the response for the "regions" intent
        Args: str
            kb_response: the response from dialog flow
            country_name: the current country
            dislikes: list of forbidden words to suggest
        Returns: str
      a response to give to the user (either client created or dialogflow created)
    """
    locations = locationtagger.find_locations(text=kb_response)
    region_words = locations.regions
    if len(region_words) > 0:
        return 'Make sure to spend plenty of time in the regions of ' + create_word_list_string(
            [region for region in region_words if not any(dislike in region.lower() for dislike in dislikes)]) + "."
    sents = sent_tokenize(kb_response)
    for sentence in sents:
        if any(dislike in sentence for dislike in dislikes):
            continue
        else:
            return sentence


def form_destinations_intent_response(kb_response: str, country_name: str, dislikes: List[str]) -> str:
    """
    Formats the response for the "other destinations" intent
        Args: str
            kb_response: the response from dialog flow
            country_name: the current country
            dislikes: list of forbidden words to suggest
        Returns: str
      a response to give to the user (either client created or dialogflow created)
    """
    locations = locationtagger.find_locations(text=kb_response)
    location_words = locations.regions + locations.cities
    if len(location_words) > 0:
        return 'Here are some great spots to check out - ' + create_word_list_string(
            [location for location in location_words[:5] if not any(dislike in location.lower() for dislike in dislikes)])
    sents = sent_tokenize(kb_response)
    for sentence in sents:
        if any(dislike in sentence for dislike in dislikes):
            continue
        else:
            return sentence


def form_get_in_intent_response(kb_response: str, country_name: str, dislikes: List[str]) -> str:
    """
    Formats the response for the "get in" intent
        Args: str
            kb_response: the response from dialog flow
            country_name: the current country
            dislikes: list of forbidden words to suggest
        Returns: str
      a response to give to the user (either client created or dialogflow created)
    """
    sents = sent_tokenize(kb_response)
    for sentence in sents:
        if any(dislike in sentence for dislike in dislikes):
            continue
        else:
            return sentence


def form_get_around_intent_response(kb_response: str, country_name: str, dislikes: List[str]) -> str:
    """
    Formats the response for the "get around" intent
        Args: str
            kb_response: the response from dialog flow
            country_name: the current country
            dislikes: list of forbidden words to suggest
        Returns: str
      a response to give to the user (either client created or dialogflow created)
    """
    sents = sent_tokenize(kb_response)
    for sentence in sents:
        if any(dislike in sentence for dislike in dislikes):
            continue
        else:
            return sentence


def form_see_intent_response(kb_response: str, country_name: str, dislikes: List[str], current_kbid_doc_mapping: dict) -> str:
    """
    Formats the response for the "see" intent
        Args: str
            kb_response: the response from dialog flow
            country_name: the current country
            dislikes: list of forbidden words to suggest
            current_kbid_doc_mapping: to use knowledgebase documents
        Returns: str
      a response to give to the user (either client created or dialogflow created)
    """
    article = get_raw_kb_text(current_kbid_doc_mapping['See'])
    banned_words = [country_name, 'City']
    sites = get_proper_nouns(article, banned_words, 5)
    if len(sites) > 0:
        return "Make sure you don't miss " + create_word_list_string(
            [x for x in sites if not any(dislike in x.lower() for dislike in dislikes)]
        ) + " while you are in " + country_name + '.'
    sents = sent_tokenize(kb_response)
    for sentence in sents:
        if any(dislike in sentence for dislike in dislikes):
            continue
        else:
            return sentence


def form_do_intent_response(kb_response: str, country_name: str, dislikes: List[str], current_kbid_doc_mapping: dict) -> str:
    """
    Formats the response for the "do" intent
        Args: str
            kb_response: the response from dialog flow
            country_name: the current country
            dislikes: list of forbidden words to suggest
            current_kbid_doc_mapping: to use knowledgebase documents
        Returns: str
      a response to give to the user (either client created or dialogflow created)
    """
    article = get_raw_kb_text(current_kbid_doc_mapping['Do'])
    banned_words = [country_name, 'City']
    sites = get_proper_nouns(article, banned_words, 5)
    if len(sites) > 0:
        return "Some fun events include " + create_word_list_string(
            [x for x in sites if not any(dislike in x.lower() for dislike in dislikes)]
        ) + '.'
    sents = sent_tokenize(kb_response)
    for sentence in sents:
        if any(dislike in sentence for dislike in dislikes):
            continue
        else:
            return sentence


def form_talk_intent_response(kb_response: str, country_name: str, dislikes: List[str], current_kbid_doc_mapping: dict) -> str:
    """
    Formats the response for the "talk" intent
        Args: str
            kb_response: the response from dialog flow
            country_name: the current country
            dislikes: list of forbidden words to suggest
            current_kbid_doc_mapping: to use knowledgebase documents
        Returns: str
      a response to give to the user (either client created or dialogflow created)
    """
    language_synsets = [
        wn.synset('language.n.01')
    ]
    article = get_raw_kb_text(current_kbid_doc_mapping['Talk'])
    banned_words = [
        'basic',
        'phrase',
        'phrases',
        'language',
        'northern',
        'southern',
        'eastern',
        'western'
    ]

    language_words = get_most_frequent_words_in_synsets(article, language_synsets, 3, 0.2, banned_words)
    languages = [x.capitalize() for x in language_words if not any(dislike in x.lower() for dislike in dislikes)]
    if len(languages) > 0:
        response = 'The most commonly spoken language in ' + country_name + ' is ' + languages[0] + '. '
        if len(languages) > 1:
            response += 'However, you will find that people also speak ' + create_word_list_string(languages[1:]) + '.'
        return response
    sents = sent_tokenize(kb_response)
    for sentence in sents:
        if any(dislike in sentence for dislike in dislikes):
            return ''
        else:
            return sentence


def form_buy_intent_response(kb_response: str, country_name: str, dislikes: List[str], current_kbid_doc_mapping: dict) -> str:
    """
    Formats the response for the "buy" intent
        Args: str
            kb_response: the response from dialog flow
            country_name: the current country
            dislikes: list of forbidden words to suggest
        Returns: str
      a response to give to the user (either client created or dialogflow created)
    """
    currency_synsets = [
        wn.synset('monetary_unit.n.01')
    ]
    banned_words = [
        'money',
        'cash',
        'coins',
        'coin',
        'banknote',
        'banknotes'
    ]
    article = get_raw_kb_text(current_kbid_doc_mapping['Buy'])
    currency_word = get_most_frequent_words_in_synsets(article, currency_synsets, 1, banned_words=banned_words)
    if len(currency_word) > 0:
        return 'To go shopping in ' + country_name + ', you will need to use the local currency, the ' + currency_word[0] + '.'
    return ''


def form_eat_intent_response(kb_response: str, country_name: str, dislikes: List[str],
                             current_kbid_doc_mapping: dict) -> str:
    """
    Formats the response for the "eat" intent
        Args: str, str, List[str], dict
            kb_response: the response from dialog flow
            country_name: the current country
            dislikes: list of forbidden words to suggest
            current_kbid_doc_mapping: to use knowledge base documents
        Returns: str
      a response to give to the user (either client created or dialogflow created)
    """
    food_synsets = [
        wn.synset('food.n.01'),
        wn.synset('fruit.n.01'),
        wn.synset('vegetable.n.01'),
        wn.synset('meat.n.01'),
        wn.synset('snack.n.01'),
        wn.synset('dessert.n.01')
    ]

    article = get_raw_kb_text(current_kbid_doc_mapping['Eat'])

    # food words that appear frequently and are not useful
    banned_words = [
        'food',
        'fruit',
        'vegetable',
        'dessert',
        'snack',
        'butter',
        'potatoes',
        'potato',
        'lunch',
        'dinner',
        'breakfast',
        'candy',
        'meal',
        'meals',
        'halal'
    ]

    food_words = get_most_frequent_words_in_synsets(article, food_synsets, 5, 0.05, banned_words)
    if len(food_words) > 0:
        return 'I recommend ordering ' + create_word_list_string(food_words) + ' from a local restaurant.'
    return sent_tokenize(kb_response)[0]


def form_drink_intent_response(kb_response: str, country_name: str, dislikes: List[str],
                               current_kbid_doc_mapping: dict) -> str:
    """
    Formats the response for the "drink" intent
        Args: str
            kb_response: the response from dialog flow
            country_name: the current country
            dislikes: list of forbidden words to suggest
             current_kbid_doc_mapping: to use knowledgebase documents
        Returns: str
      a response to give to the user (either client created or dialogflow created)
    """
    drink_synsets = [
        wn.synset('drink.n.01'),
        wn.synset('alcohol.n.01'),
        wn.synset('beverage.n.01'),
    ]

    # drink words that appear frequently and are not useful
    banned_words = [
        'alcohol',
        'beverage',
        'beverages',
        'drink',
        'water'
    ]

    article = get_raw_kb_text(current_kbid_doc_mapping['Drink'])

    drink_words = get_most_frequent_words_in_synsets(article, drink_synsets, 5, 0.05, banned_words)
    if len(drink_words) > 0:
        return 'The best drinks to try in ' + country_name + ' are ' + create_word_list_string(drink_words) + '.'
    return sent_tokenize(kb_response)[0]


def form_sleep_intent_response(kb_response: str, country_name: str, dislikes: List[str]) -> str:
    """
    Formats the response for the "sleep" intent
        Args: str
            kb_response: the response from dialog flow
            country_name: the current country
            dislikes: list of forbidden words to suggest
        Returns: str
      a response to give to the user (either client created or dialogflow created)
    """
    sents = sent_tokenize(kb_response)
    for sentence in sents:
        if any(dislike in sentence for dislike in dislikes):
            continue
        else:
            return sentence


def form_stay_healthy_intent_response(kb_response: str, country_name: str, dislikes: List[str]) -> str:
    """
    Formats the response for the "stay healtyh" intent
        Args: str
            kb_response: the response from dialog flow
            dislikes: list of forbidden words to suggest
        Returns: str
      a dialogflow created response to give to the user
    """
    sents = sent_tokenize(kb_response)
    for sentence in sents:
        if any(dislike in sentence for dislike in dislikes):
            continue
        else:
            return sentence


def form_stay_safe_intent_response(kb_response: str, country_name: str, dislikes: List[str]) -> str:
    """
    Formats the response for the "stay safe" intent
        Args: str
            kb_response: the response from dialog flow
            dislikes: list of forbidden words to suggest
        Returns: str
      a dialogflow created response to give to the user
    """
    sents = sent_tokenize(kb_response)
    for sentence in sents:
        if any(dislike in sentence for dislike in dislikes):
            continue
        else:
            return sentence


def form_connect_intent_response(kb_response: str, country_name: str, dislikes: List[str]) -> str:
    """
    Formats the response for the "connect" intent
        Args: str
            kb_response: the response from dialog flow
            dislikes: list of forbidden words to suggest
        Returns: str
      a dialogflow created response to give to the user
    """
    sents = sent_tokenize(kb_response)
    for sentence in sents:
        if any(dislike in sentence for dislike in dislikes):
            continue
        else:
            return sentence


def form_respect_intent_response(kb_response: str, country_name: str, dislikes: List[str]) -> str:
    """
    Formats the response for the "respect" intent
        Args: str
            kb_response: the response from dialog flow
            dislikes: list of forbidden words to suggest
        Returns: str
      a dialogflow created response to give to the user
    """
    sents = sent_tokenize(kb_response)
    for sentence in sents:
        if any(dislike in sentence for dislike in dislikes):
            continue
        else:
            return sentence


def kb_intent_response(kb_response: str, intent_name: str, country_name: str, user_dict: dict,
                       current_kbid_doc_mapping: Optional[dict] = None) -> str:
    """
    Maps the intent to the correct function to build a response
        Args: str, str, str, dict
            kb_response: the response from dialog flow
            intent: name of the triggered intent
            country_name: the name of the current country
            user_dict: the current knowledge about the user
        Returns: str
     a response to give to the user (either client created or dialogflow created)
    """
    dislikes = user_dict["dislikes"]
    if intent_name == "Understand":
        return form_understand_intent_response(kb_response, country_name, dislikes)
    elif intent_name == "Regions":
        return form_regions_intent_response(kb_response, country_name, dislikes)
    elif intent_name == "Cities":
        return form_cities_intent_response(kb_response, country_name, dislikes)
    elif intent_name == "Other_destinations":
        return form_destinations_intent_response(kb_response, country_name, dislikes)
    elif intent_name == "Get_in":
        return form_get_in_intent_response(kb_response, country_name, dislikes)
    elif intent_name == "Get_around":
        return form_get_around_intent_response(kb_response, country_name, dislikes)
    elif intent_name == "See":
        return form_see_intent_response(kb_response, country_name, dislikes, current_kbid_doc_mapping)
    elif intent_name == "Do":
        return form_do_intent_response(kb_response, country_name, dislikes, current_kbid_doc_mapping)
    elif intent_name == "Talk":
        return form_talk_intent_response(kb_response, country_name, dislikes, current_kbid_doc_mapping)
    elif intent_name == "Buy":
        return form_buy_intent_response(kb_response, country_name, dislikes, current_kbid_doc_mapping)
    elif intent_name == "Eat":
        return form_eat_intent_response(kb_response, country_name, dislikes, current_kbid_doc_mapping)
    elif intent_name == "Drink":
        return form_drink_intent_response(kb_response, country_name, dislikes, current_kbid_doc_mapping)
    elif intent_name == "Sleep":
        return form_sleep_intent_response(kb_response, country_name, dislikes)
    elif intent_name == "Stay_healthy":
        return form_stay_healthy_intent_response(kb_response, country_name, dislikes)
    elif intent_name == "Stay_safe":
        return form_stay_safe_intent_response(kb_response, country_name, dislikes)
    elif intent_name == "Connect":
        return form_connect_intent_response(kb_response, country_name, dislikes)
    elif intent_name == "Respect":
        return form_respect_intent_response(kb_response, country_name, dislikes)