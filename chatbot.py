from google.protobuf.json_format import MessageToDict
from KnowledgeBase import create_knowledge_base, HEADER_LIST
from IntentParsing import *
from common_functions import *

if __name__ == '__main__':
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(PROJECT_ID, 'current-user-id')
    user_dict = {"name": "", "countries": [], "interests": [], "dislikes": []}

    current_kbid = None
    current_kbid_doc_mapping = None
    user_input = 'Hello'
    filename = None
    country = None

    is_first_request = True

    while user_input != 'exit':
        response = make_dialogflow_request(session, session_client, user_input, None)

        # convert response to a dictionary for parsing
        response_dict = MessageToDict(response.query_result._pb)

        # collect information about the user
        parameters_dict = response_dict['parameters']
        should_skip = False
        if 'person' in parameters_dict and is_first_request:
            if 'name' in parameters_dict['person']:
                user_name = parameters_dict['person']['name']
                print("LOG - Detected new user: " + user_name)
                filename = f"{user_name}.json"
                if not os.path.exists(filename):
                    user_dict["name"] = user_name
                    save_user_data(filename, user_dict)
                else:
                    user_dict = load_user_data(filename)
                    if len(user_dict["countries"]) > 0:
                        last_country = user_dict["countries"][-1]
                        print(
                            f"Welcome back {user_name}, let's continue researching your trip to {last_country}!")
                        user_input = f"I want to go to {last_country}"
                        make_dialogflow_request(session, session_client, user_input, None)
                        response = {}
                        response_dict = {}
                        parameters_dict = {'geo-country':last_country}
                    else:
                        print(f"Welcome back {user_name}, how can I help you today?")
                        user_input = input()
                is_first_request = False

        # country detected
        if 'geo-country' in parameters_dict and parameters_dict['geo-country'] != '':
            # check if it's the same country in the current context and resend without the name
            if country == parameters_dict['geo-country']:
                user_input = user_input.lower().replace(country.lower(), 'it')
                response = make_dialogflow_request(session, session_client, user_input, None)

                # convert response to a dictionary for parsing
                response_dict = MessageToDict(response.query_result._pb)

                # collect information about the user
                parameters_dict = response_dict['parameters']

                if 'intent' in response_dict and 'displayName' in response_dict['intent']:
                    intent_name = response_dict['intent']['displayName']
                    if intent_name == 'Default Fallback' or intent_name == 'Talk':
                        should_skip = True
            else:
                country = parameters_dict['geo-country']
                print("LOG - Detected country: " + country)

                if country in CURRENT_COUNTRIES:
                    current_kbid = get_kb_name_of_country(country)
                else:
                    # build a knowledge base for that country if it does not already exist
                    current_kbid = create_knowledge_base(country)
                    CURRENT_COUNTRIES.append(country)
                current_kbid_doc_mapping = map_doc_name_to_id(current_kbid)
                user_dict["countries"].append(country)

        # extract what information the user would like to know
        if 'intent' in response_dict and 'displayName' in response_dict['intent'] and not should_skip:
            intent_name = response_dict['intent']['displayName']
            print("LOG - Detected user intent: " + intent_name)
            if intent_name == "Welcome Intent" and user_dict["name"] != '':
                print("How can I help you today?")
            elif intent_name == "Dislike":
                disliked = parameters_dict['Disliked']
                user_dict["dislikes"].append(disliked)
                print(response.query_result.fulfillment_text)
            elif intent_name == "Default Fallback" and not should_skip:
                print("EXPERIMENTAL DEFAULT FALLBACK")
                response = make_dialogflow_request(session, session_client, user_input, current_kbid)
                answers = response.query_result.knowledge_answers.answers
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
                            print(sentence)
                            found_result = True
                        x+=1

                    if not found_result:
                        print("Sorry, can you rephrase your question?")
                else:
                    print("Sorry, I didn't get that.")
            elif not should_skip:
                # check if we should reference the knowledge base of a certain header
                if intent_name in HEADER_LIST and country:
                    user_dict["interests"].append(intent_name)
                    kb_response = search_knowledge_base_by_intent(session, session_client, user_input, current_kbid,
                                                                  intent_name, current_kbid_doc_mapping)
                    if kb_response is not None:
                        print(
                            response.query_result.fulfillment_text + ' ' + kb_intent_response(kb_response, intent_name,
                                                                                              country, user_dict,
                                                                                              current_kbid_doc_mapping))
                    else:
                        print(response.query_result.fulfillment_text)
                else:
                    print(response.query_result.fulfillment_text)
        else:
            if 'query_result' in response:
                print(response.query_result.fulfillment_text)

        if filename:
            save_user_data(filename, user_dict)
        user_input = input()