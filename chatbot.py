import re
from typing import Union

from google.cloud.dialogflow_v2beta1 import SessionsClient
from google.protobuf.json_format import MessageToDict
from KnowledgeBase import create_knowledge_base, HEADER_LIST
from IntentParsing import *
from common_functions import *


def default_kb_search(session: str, session_client: SessionsClient, user_input: str, current_kbid: str) -> str:
    """
    returns a Dialogflow knowledge base response from the entire country knowledge base
    Args: str, SessionsClient, str, str
        session: the name of the ongoing Dialogflow session
        session_client: the client accepting Dialogflow requests
        user_input: the input the user typed in
        current_kbid: the knowledge base you want to query
    Returns: str
        the response that was found from the knowledge base (or a default fallback)
    """
    response = make_dialogflow_request(session, session_client, user_input, current_kbid)
    answers = response.query_result.knowledge_answers.answers
    if len(answers) > 0:
        answer = answers[0].answer
        x = 0
        while x < len(nltk.sent_tokenize(answer)):
            sentence = nltk.sent_tokenize(answer)[x]

            # check if the response shares a word in common with the user's input
            has_word_in_common = False
            for word in nltk.word_tokenize(user_input):
                if len(word) > 4 and sentence.lower().find(word.lower()) != -1:
                    has_word_in_common = True

            if len(sentence.split()) < 100 and has_word_in_common:
                return "Here's what I found about that on the web: " + sentence
            x += 1
        return "Sorry, can you rephrase your question?"
    else:
        return "Sorry, I didn't get that."


def add_disliked_item(disliked_input: str, user_dict: dict[str, Union[str, list, dict]]) -> None:
    """
    adds a user dislike to their dictionary
    Args: str, dict[str, Union[str, list, dict]]
        disliked_input: the string including the item the user dislikes
        user_dict: the user's dictionary which includes their dislikes
    Returns: None
    """
    for word in disliked_input.lower().split():
        pos_tags = nltk.pos_tag([word])
        if 'N' in pos_tags[0][1] and word not in user_dict["dislikes"]:
            user_dict["dislikes"].append(word)


if __name__ == '__main__':
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(PROJECT_ID, 'current-user-id')
    user_dict = {"name": "", "countries": [], "interests": {}, "dislikes": []}

    current_kbid = None
    current_kbid_doc_mapping = None
    user_input = 'Hello'
    filename = None
    country = None

    is_first_request = True

    while user_input != 'exit':
        user_input = user_input.lower()
        if country and country.lower() in user_input:
            user_input = re.sub(country.lower(), "", user_input)
        response = make_dialogflow_request(session, session_client, user_input, None)

        # convert response to a dictionary for parsing
        response_dict = MessageToDict(response.query_result._pb)

        # collect information about the user
        parameters_dict = response_dict['parameters']

        # case where we are loading the user context for the first time
        if 'person' in parameters_dict and is_first_request and 'name' in parameters_dict['person']:
            user_name = parameters_dict['person']['name']
            filename = f"{user_name}.json"
            if not os.path.exists(filename):
                user_dict["name"] = user_name
                save_user_data(filename, user_dict)
                print(
                    f"Nice to meet you {user_name}, what country are you interested in visiting?")
            else:
                user_dict = load_user_data(filename)

                # user has previous countries in their JSON
                if len(user_dict["countries"]) > 0:
                    last_country = user_dict["countries"][-1]
                    print(
                        f"Welcome back {user_name}, let's continue researching your trip to {last_country}!")

                    # load the current country context into Dialogflow
                    user_input = f"I want to go to {last_country}"
                    make_dialogflow_request(session, session_client, user_input, None)

                    # avoid showing the response from this extra request to the user
                    response = {}
                    response_dict = {}
                    parameters_dict = {'geo-country': last_country}

                # existing user has never indicated interest in a country
                else:
                    print(f"Welcome back {user_name}, please let me know the name of a country you are interested in.")
            is_first_request = False

        # new country detected, so you should switch context
        if 'geo-country' in parameters_dict and parameters_dict['geo-country'] != '':
            country = parameters_dict['geo-country']

            if country in CURRENT_COUNTRIES:
                current_kbid = get_kb_name_of_country(country)
            else:
                # build a knowledge base for that country if it does not already exist
                current_kbid = create_knowledge_base(country)
                CURRENT_COUNTRIES.append(country)
                print("Generating knowledge base for " + country + ". Note: this may take several minutes.")
            current_kbid_doc_mapping = map_doc_name_to_id(current_kbid)

            # update the user dict so this country is now the most recent
            if country in user_dict["countries"]:
                user_dict["countries"].remove(country)
            user_dict["countries"].append(country)

        # extract what information the user would like to know
        if 'intent' in response_dict and 'displayName' in response_dict['intent']:
            intent_name = response_dict['intent']['displayName']

            # if you are in the Dislike flow, add the disliked item
            if intent_name == "Dislike":
                add_disliked_item(parameters_dict['Disliked'], user_dict)
                print(response.query_result.fulfillment_text)

            # if no intent was detected, go to the default knowledge base flow
            elif intent_name == "Default Fallback":
                print(default_kb_search(session, session_client, user_input, current_kbid))

            # if an article header intent is detected, call the intent-specific parsing logic
            elif intent_name in HEADER_LIST and country:

                # update the user dict with their interests
                if intent_name in user_dict["interests"]:
                    user_dict["interests"][intent_name] += 1
                else:
                    user_dict["interests"][intent_name] = 1

                # check whether the entire knowledge base has been loaded
                if len(current_kbid_doc_mapping) < 16:
                    current_kbid_doc_mapping = map_doc_name_to_id(current_kbid)

                kb_response = search_knowledge_base_by_intent(session, session_client, user_input, current_kbid,
                                                              intent_name, current_kbid_doc_mapping)
                if kb_response is None:
                    kb_response = ''
                result = response.query_result.fulfillment_text + ' ' + kb_intent_response(kb_response, intent_name,
                                                                                  country, user_dict,
                                                                                  current_kbid_doc_mapping)
                if result == '':
                    print("Sorry, I didn't get that.")
                else:
                    print(result)

            elif intent_name == "Goodbye":
                print("Goodbye!")
                exit(0)
            else:
                print(response.query_result.fulfillment_text)

        if filename:
            save_user_data(filename, user_dict)
        user_input = input()
