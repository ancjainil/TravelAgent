import os

from google.cloud import dialogflow_v2beta1 as dialogflow
from google.protobuf.json_format import MessageToDict
from KnowledgeBase import create_knowledge_base, HEADER_LIST
from chatbot import search_knowledge_base_by_intent, add_disliked_item
from common_functions import *
from IntentParsing import *

from flask import Flask, request

app = Flask(__name__)

filename = None
country = None
current_kbid = None
current_kbid_doc_mapping = None
is_first_request = True
flag = False
last_country = None
session = None

user_dict = {"name": "", "countries": [], "interests": {}, "dislikes": []}


@app.route('/webhook', methods=["POST"])
def webhook():
    response = {'fulfillmentText': ""}

    global filename
    global country
    global current_kbid
    global current_kbid_doc_mapping
    global user_dict
    global is_first_request
    global flag
    global last_country
    global session
    global session_id

    # get request
    payload = request.json

    # set up session
    session_client = dialogflow.SessionsClient()

    user_input = payload["queryResult"]["queryText"]
    parameters_dict = payload["queryResult"]['parameters']

    # person detected
    if 'person' in parameters_dict and 'name' in parameters_dict['person']:
            user_name = parameters_dict['person']['name']
            print("Log - Detected name: " + user_name)
            filename = f"{user_name}.json"
            if not os.path.exists(filename):
                user_dict["name"] = user_name
                save_user_data(filename, user_dict)
            else:
                user_dict = load_user_data(filename)


                if len(user_dict["countries"]) > 0:
                    last_country = user_dict["countries"][-1]
                    response[
                        "fulfillmentText"] = f"Welcome back {user_name}, let's continue researching your trip to {last_country}!"

                    session = session_client.session_path(PROJECT_ID, user_name)
                    print(f"DEBUG LOG session - {session}")
                    country = last_country
                    current_kbid = get_kb_name_of_country(country)
                    current_kbid_doc_mapping = map_doc_name_to_id(current_kbid)
                    return response
                else:
                    response["fulfillmentText"] = f"Welcome back {user_name}, how can I help you today?"
                    session = session_client.session_path(PROJECT_ID, user_name)
                    return response

    # returning user detected

    if 'geo-country' in parameters_dict and parameters_dict['geo-country'] != '':
        country = parameters_dict['geo-country']
        print("LOG - Detected country: " + country)

        if country in CURRENT_COUNTRIES:
            current_kbid = get_kb_name_of_country(country)
        else:
            # build a knowledge base for that country if it does not already exist
            current_kbid = create_knowledge_base(country)
            CURRENT_COUNTRIES.append(country)

        current_kbid_doc_mapping = map_doc_name_to_id(current_kbid)
        if country in user_dict["countries"]:
            user_dict["countries"].remove(country)
        user_dict["countries"].append(country)

    if filename:
        save_user_data(filename, user_dict)

    # extract what information the user would like to know
    query_result = payload["queryResult"]

    if "fulfillmentText" in query_result:
        fulfill = query_result["fulfillmentText"]
    if 'intent' in payload["queryResult"]:
        print("DEBUG LOG  - IN ITENT")
        intent_name = query_result['intent']['displayName']
        print("LOG - Detected user intent: " + intent_name)
        # dislike
        if intent_name == "Dislike":
            add_disliked_item(parameters_dict['Disliked'], user_dict)
            return response
        # close
        elif intent_name == "Close":
            response["fulfillmentText"] = fulfill
            return response

        # default
        elif intent_name == "Default Fallback":
            print("EXPERIMENTAL DEFAULT FALLBACK")

            response2 = make_dialogflow_request(session, session_client, user_input, current_kbid)
            answers = response2.query_result.knowledge_answers.answers
            if len(answers) > 0:
                answer = answers[0].answer
                x = 0
                found_result = False
                while x < len(nltk.sent_tokenize(answer)) and not found_result:
                    sentence = nltk.sent_tokenize(answer)[x]
                    has_word_in_common = False
                    for word in nltk.word_tokenize(user_input):
                        if len(word) > 4 and sentence.lower().find(word.lower()) != -1:
                            has_word_in_common = True
                    if len(sentence.split()) < 100 and has_word_in_common:
                        response["fulfillmentText"] = f"Here's what I found about that on the web: {sentence}"
                        return response
                    x += 1

                response["fulfillmentText"] = f"Sorry, can you rephrase your question?"
                return response
            else:
                response["fulfillmentText"] = f"Sorry, I didn't get that."
                return response

        # other
        else:
            # check if we should reference the knowledge base of a certain header
            if intent_name in HEADER_LIST and country:
                if "fulfillmentText" in query_result:
                    fulfill = query_result["fulfillmentText"]
                else:
                    fulfill = ""

                if intent_name in user_dict["interests"]:
                    user_dict["interests"][intent_name] += 1
                else:
                    user_dict["interests"][intent_name] = 1
                if filename:
                    save_user_data(filename, user_dict)
                print("DEBUG LOG - HERE 1")
                kb_response = search_knowledge_base_by_intent(session, session_client, user_input, current_kbid,
                                                              intent_name, current_kbid_doc_mapping)
                if kb_response is None:
                    print("DEBUG LOG - HERE 2")
                    kb_response = ''
                    content = kb_intent_response(kb_response, intent_name, country, user_dict, current_kbid_doc_mapping)
                    if content is None:
                        content = " "
                    response["fulfillmentText"] = f"{fulfill} {content}"
                    return response
                else:
                    print("DEBUG LOG - HERE 3")
                    content = kb_intent_response(kb_response, intent_name, country, user_dict, current_kbid_doc_mapping)
                    response["fulfillmentText"] = f"{fulfill} {content}"
                    return response
            else:
                response["fulfillmentText"] = fulfill
                return response
    else:
        response["fulfillmentText"] = fulfill
        return response


if __name__ == '__main__':
    app.run(port=5002)