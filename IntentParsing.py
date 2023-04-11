from typing import List, Optional
from nltk.corpus import wordnet as wn
from nltk.tokenize import sent_tokenize
from google.cloud import dialogflow_v2beta1 as df
import locationtagger
import warnings
import operator


def get_raw_kb_text(doc_name: str) -> str:
    client = df.DocumentsClient()
    return str(client.get_document(name=doc_name))

def get_most_frequent_words_in_synsets(text: str, synsets: List[str], num_to_return: int, banned_words: Optional[List[str]] = []) -> List[str]:
    warnings.filterwarnings('ignore')

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
                        if word in word_counts:
                            word_counts[word] += 1
                        # check if singular form of word is already counted
                        elif len(word) > 1 and word[:len(word)-1] in word_counts:
                            word_counts[word[:len(word)-1]] += 1
                        # check if plural form of word is already counted
                        elif word + 's' in word_counts:
                            word_counts[ word + 's'] += 1
                        else:
                            word_counts[word] = 1
    sorted_words = sorted(word_counts.items(), key=operator.itemgetter(1), reverse=True)

    result = []
    x = 0
    while x < len(sorted_words) and x < num_to_return:
        result.append(sorted_words[x][0])
        x+=1
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
def form_understand_intent_response(kb_response: str) -> str:
    return sent_tokenize(kb_response)[0]

def form_cities_intent_response(kb_response: str, country_name: str) -> str:
    locations = locationtagger.find_locations(text=kb_response)
    city_words = locations.cities
    if len(city_words) > 0:
        return 'Here are the best cities to visit in ' + country_name + ': ' + create_word_list_string(city_words)
    return sent_tokenize(kb_response)[0]
def form_regions_intent_response(kb_response: str, country_name: str) -> str:
    locations = locationtagger.find_locations(text=kb_response)
    region_words = locations.regions
    if len(region_words) > 0:
        return 'Here are the best areas of ' + country_name + 'to visit: ' + create_word_list_string(region_words)
    return sent_tokenize(kb_response)[0]

def form_destinations_intent_response(kb_response: str, country_name: str) -> str:
    locations = locationtagger.find_locations(text=kb_response)
    location_words = locations.regions + locations.cities
    if len(location_words) > 0:
        return 'Here are some great spots to check out ' + country_name + ': ' + create_word_list_string(location_words)
    return sent_tokenize(kb_response)[0]

def form_get_in_intent_response(kb_response: str, country_name: str) -> str:
    transport_synsets = [
        wn.synset('transportation.n.01'),
        wn.synset('vehicle.n.01'),
        wn.synset('car.n.01'),
        wn.synset('bus.n.01'),
        wn.synset('train.n.01'),
        wn.synset('aircraft.n.01'),
        wn.synset('ship.n.01'),
        wn.synset('boat.n.01'),
        wn.synset('helicopter.n.01'),
    ]

    transport_words = get_words_in_synsets(kb_response, transport_synsets)
    if len(transport_words) > 0:
        return 'To get to ' + country_name + ', I recommend one of the following methods of transportation: ' + create_word_list_string(
            transport_words)
    return sent_tokenize(kb_response)[0]

def form_get_around_intent_response(kb_response: str, country_name: str) -> str:
    transport_synsets = [
        wn.synset('transportation.n.01'),
        wn.synset('vehicle.n.01'),
        wn.synset('car.n.01'),
        wn.synset('bus.n.01'),
        wn.synset('train.n.01'),
        wn.synset('subway.n.01'),
        wn.synset('tram.n.01'),
        wn.synset('aircraft.n.01'),
        wn.synset('taxi.n.01'),
        wn.synset('ship.n.01'),
        wn.synset('boat.n.01'),
        wn.synset('bicycle.n.01'),
        wn.synset('motorcycle.n.01'),
        wn.synset('scooter.n.01'),
        wn.synset('helicopter.n.01'),
    ]

    transport_words = get_words_in_synsets(kb_response, transport_synsets)
    if len(transport_words) > 0:
        return 'Here are the best ways to get around in ' + country_name + ': ' + create_word_list_string(
            transport_words)
    return sent_tokenize(kb_response)[0]

def form_see_intent_response(kb_response: str, country_name: str) -> str:
    # todo
    return sent_tokenize(kb_response)[0]

def form_do_intent_response(kb_response: str, country_name: str) -> str:
    activity_synsets = [
        wn.synset('do.v.01'),
        wn.synset('play.v.01'),
        wn.synset('participate.v.01'),
        wn.synset('practice.v.01'),
        wn.synset('explore.v.01'),
        wn.synset('discover.v.01')
    ]

    activity_words = get_words_in_synsets(kb_response, activity_synsets)
    if len(activity_words) > 0:
        return 'You can engage in all kinds of activities, like ' + create_word_list_string(
            activity_words)
    return sent_tokenize(kb_response)[0]

def form_talk_intent_response(kb_response: str, country_name: str) -> str:
    language_synsets = [
        wn.synset('language.n.01')
    ]

    language_words = get_words_in_synsets(kb_response, language_synsets)
    if len(language_words) > 0:
        return 'Here are the languages that are spoken in ' + country_name + ': ' + create_word_list_string(language_words)
    return sent_tokenize(kb_response)[0]

def form_buy_intent_response(kb_response: str, country_name: str) -> str:
    product_synsets = [
        wn.synset('product.n.01'),
        wn.synset('product.n.02'),
        wn.synset('product.n.03'),
        wn.synset('commodity.n.01'),
        wn.synset('merchandise.n.01'),
        wn.synset('article.n.01')
    ]

    product_words = get_words_in_synsets(kb_response, product_synsets)
    if len(product_words) > 0:
        return 'Here are the best things you can buy in ' + country_name + ': ' + create_word_list_string(
            product_words)
    return sent_tokenize(kb_response)[0]

def form_eat_intent_response(kb_response: str, country_name: str, current_kbid_doc_mapping: dict) -> str:
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
        'candy'
    ]

    food_words = get_most_frequent_words_in_synsets(article, food_synsets, 5, banned_words)
    if len(food_words) > 0:
        return 'I recommend ordering ' + create_word_list_string(food_words) + ' from a local restaurant.'
    return sent_tokenize(kb_response)[0]

def form_drink_intent_response(kb_response: str, country_name: str, current_kbid_doc_mapping: dict) -> str:
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

    drink_words = get_most_frequent_words_in_synsets(article, drink_synsets, 5, banned_words)
    if len(drink_words) > 0:
        return 'The best drinks to try in ' + country_name + ' are ' + create_word_list_string(drink_words) + '.'
    return sent_tokenize(kb_response)[0]
def form_sleep_intent_response(kb_response: str, country_name: str) -> str:
    lodging_synsets = [
        wn.synset('lodging.n.01'),
        wn.synset('hotel.n.01'),
        wn.synset('motel.n.01'),
        wn.synset('resort.n.01'),
        wn.synset('guesthouse.n.01'),
        wn.synset('inn.n.01'),
        wn.synset('boarding_house.n.01'),
        wn.synset('bed_and_breakfast.n.01'),
        wn.synset('campground.n.01'),
    ]

    lodging_words = get_words_in_synsets(kb_response, lodging_synsets)
    if len(lodging_words) > 0:
        return 'Here are the recommended options for spending your time in ' + country_name + ': ' + create_word_list_string(lodging_words)
    return sent_tokenize(kb_response)[0]
def form_stay_healthy_intent_response(kb_response: str, country_name: str) -> str:
    return sent_tokenize(kb_response)[0]

def form_stay_safe_intent_response(kb_response: str, country_name: str) -> str:
    return sent_tokenize(kb_response)[0]

def form_connect_intent_response(kb_response: str, country_name: str) -> str:
    return sent_tokenize(kb_response)[0]

def form_respect_intent_response(kb_response: str, country_name: str) -> str:
    return sent_tokenize(kb_response)[0]
def kb_intent_response(kb_response: str, intent_name: str, country_name: str, current_kbid_doc_mapping: Optional[dict] = None) -> str:
    if intent_name == "Understand":
        return form_understand_intent_response(kb_response, country_name)
    elif intent_name == "Regions":
        return form_regions_intent_response(kb_response, country_name)
    elif intent_name == "Cities":
        return form_cities_intent_response(kb_response, country_name)
    elif intent_name == "Other_destinations":
        return form_destinations_intent_response(kb_response, country_name)
    elif intent_name == "Get_in":
        return form_get_in_intent_response(kb_response, country_name)
    elif intent_name == "Get_around":
        return form_get_around_intent_response(kb_response, country_name)
    elif intent_name == "See":
        return form_see_intent_response(kb_response, country_name)
    elif intent_name == "Do":
        return form_do_intent_response(kb_response, country_name)
    elif intent_name == "Talk":
        return form_talk_intent_response(kb_response, country_name)
    elif intent_name == "Buy":
        return form_buy_intent_response(kb_response, country_name)
    elif intent_name == "Eat":
        return form_eat_intent_response(kb_response, country_name, current_kbid_doc_mapping)
    elif intent_name == "Drink":
        return form_drink_intent_response(kb_response, country_name,  current_kbid_doc_mapping)
    elif intent_name == "Sleep":
        return form_sleep_intent_response(kb_response, country_name)
    elif intent_name == "Stay_healthy":
        return form_stay_healthy_intent_response(kb_response, country_name)
    elif intent_name == "Stay_safe":
        return form_stay_safe_intent_response(kb_response, country_name)
    elif intent_name == "Connect":
        return form_connect_intent_response(kb_response, country_name)
    elif intent_name == "Respect":
        return form_respect_intent_response(kb_response, country_name)

if __name__ == '__main__':
    print(form_regions_intent_response(' you can go to quebec, montreal, nunavut', 'france'))