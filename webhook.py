import os

from google.cloud import dialogflow_v2beta1 as dialogflow
import requests
from IntentParsing import kb_intent_response
from KnowledgeBase import create_knowledge_base, HEADER_LIST
from chatbot import search_knowledge_base_by_intent
from common_functions import *

from flask import Flask, request


app = Flask(__name__)

response =  {'fulfillmentText': ""}

filename = None
country = None
current_kbid = None
current_kbid_doc_mapping = None
user_dict = {"name":"","countries":[], "interests":[], "dislikes": []}
CURRENT_COUNTRIES = ["Canada", "Chile", "France", "Germany","Peru", "Italy"]


@app.route('/webhook', methods = ["POST"])
def webhook():
    global filename
    global country
    global current_kbid
    global current_kbid_doc_mapping
    global user_dict

    payload = request.json
    session_id = payload["session"].split("/")[-1]
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(PROJECT_ID, session_id)

    user_input = payload["queryResult"]["queryText"]
    parameters_dict = payload["queryResult"]['parameters']

    if user_input == 'exit':
        response["fulfillmentText"] = "Thanks for stopping by"
        return response

    #person detected
    if 'person' in parameters_dict:
                user_name = parameters_dict['person']['name']
                print("Detected name: " + user_name)
                # create user model if it doesnt exist
                filename = f"{user_name}.json"
                if not os.path.exists(filename):
                        print(f"Creating file {filename} ")
                        user_dict["name"] = user_name
                        save_user_data(filename, user_dict)
                else:
                    user_dict = load_user_data(filename)
                    last_country = user_dict["countries"][-1]
                    response["fulfillmentText"] = f"Welcome back {user_name}, would you like to continue discussing about {last_country}?"
                    return response
    # country detected
    if 'geo-country' in parameters_dict:
        country = parameters_dict['geo-country']
        print("LOG - Detected country: " + country)
        if country in CURRENT_COUNTRIES:
            current_kbid = get_kb_name_of_country(country)
            print(f"Retrieved {current_kbid}")
        else:
            # build a knowledge base for that country if it does not already exist
            current_kbid = create_knowledge_base(country)
            CURRENT_COUNTRIES.append(country)
        current_kbid_doc_mapping = map_doc_name_to_id(current_kbid)
        user_dict["countries"].append(country)  
    if filename:
        save_user_data(filename, user_dict)     


     # extract what information the user would like to know
    
    query_result = payload["queryResult"]
    fulfill = query_result["fulfillmentText"]
    if 'intent' in query_result and 'displayName' in query_result['intent']:
        print(f"Retrieved {current_kbid}")
        intent_name = query_result['intent']['displayName']

        print("LOG - Detected new user intent: " + intent_name)
        # check if we should reference the knowledge base of a certain header
        if intent_name in HEADER_LIST:
            user_dict["interests"].append(intent_name)
            if filename:
                    save_user_data(filename, user_dict)
            kb_response = search_knowledge_base_by_intent(session, session_client, user_input, current_kbid, intent_name, current_kbid_doc_mapping)
            if kb_response is not None:
                content = kb_intent_response(kb_response, intent_name, country)
                response["fulfillmentText"] = f"{fulfill} {content}"
                return response
            else:
                response["fulfillmentText"] = fulfill
                return response
        else:
            response["fulfillmentText"] = fulfill
            return response
    else:
        response["fulfillmentText"] = fulfill
        return response
if __name__ == '__main__':
    app.run(port=5002)
