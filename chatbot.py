from google.cloud import dialogflow_v2beta1 as dialogflow
from google.protobuf.json_format import MessageToDict
from KnowledgeBase import create_knowledge_base, scrape


if __name__ == '__main__':
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path('s4395-travel-agent-bapg', 'current-user-id')

    user_input = 'Hello'
    while user_input != 'exit':
        text_input = dialogflow.types.TextInput(text=user_input, language_code='en-US')
        query_input = dialogflow.types.QueryInput(text=text_input)
        response = session_client.detect_intent(session=session,query_input=query_input)

        # convert response to a dictionary for parsing
        response_dict = MessageToDict(response.query_result._pb)

        # collect information about the user
        parameters_dict = response_dict['parameters']
        if 'person' in parameters_dict:
            user_name = parameters_dict['person']['name']
            print("LOG - Detected new user: " + user_name)

        # country detected
        if 'geo-country' in parameters_dict:
            country = parameters_dict['geo-country']
            print("LOG - Detected new country: " + country)
            # build a knowledge base for that country
            kb_id = create_knowledge_base(country)
            scrape(country, kb_id)

        # extract what information the user would like to know
        if 'intent' in response_dict:
            intent_name = response_dict['intent']['displayName']
            print("LOG - Detected new user intent: " + intent_name)

        endConversation = str(response.query_result.intent.display_name)
        print(response.query_result.fulfillment_text)
        user_input = input()




