def form_understand_intent_response(kb_response: str) -> str:
    return 'TODO: Understand response'

def form_regions_intent_response(kb_response: str) -> str:
    return 'TODO: Regions response'
def form_cities_intent_response(kb_response: str) -> str:
    return 'TODO: cities response'

def form_destinations_intent_response(kb_response: str) -> str:
    return 'TODO: Other Destinations response'

def form_get_in_intent_response(kb_response: str) -> str:
    return 'TODO: Get In response'

def form_get_around_intent_response(kb_response: str) -> str:
    return 'TODO: Get Around response'

def form_see_intent_response(kb_response: str) -> str:
    return 'TODO: See response'

def form_do_intent_response(kb_response: str) -> str:
    return 'TODO: Do response'

def form_talk_intent_response(kb_response: str) -> str:
    return 'TODO: Talk response'

def form_buy_intent_response(kb_response: str) -> str:
    return 'TODO: Buy response'

def form_eat_intent_response(kb_response: str) -> str:
    return 'TODO: Eat response'

def form_drink_intent_response(kb_response: str) -> str:
    return 'TODO: Drink response'
def form_sleep_intent_response(kb_response: str) -> str:
    return 'TODO: Sleep response'
def form_stay_healthy_intent_response(kb_response: str) -> str:
    return 'TODO: Stay Healthy response'

def form_stay_safe_intent_response(kb_response: str) -> str:
    return 'TODO: Stay Safe response'

def form_connect_intent_response(kb_response: str) -> str:
    return 'TODO: Connect response'

def form_respect_intent_response(kb_response: str) -> str:
    return 'TODO: Respect response'
def kb_intent_response(kb_response: str, intent_name: str) -> str:
    if intent_name == "Understand":
        return form_understand_intent_response(kb_response)
    elif intent_name == "Regions":
        return form_regions_intent_response(kb_response)
    elif intent_name == "Cities":
        return form_cities_intent_response(kb_response)
    elif intent_name == "Other destinations":
        return form_destinations_intent_response(kb_response)
    elif intent_name == "Get in":
        return form_get_in_intent_response(kb_response)
    elif intent_name == "Get around":
        return form_get_around_intent_response(kb_response)
    elif intent_name == "See":
        return form_see_intent_response(kb_response)
    elif intent_name == "Do":
        return form_do_intent_response(kb_response)
    elif intent_name == "Talk":
        return form_talk_intent_response(kb_response)
    elif intent_name == "Buy":
        return form_buy_intent_response(kb_response)
    elif intent_name == "Eat":
        return form_eat_intent_response(kb_response)
    elif intent_name == "Drink":
        return form_drink_intent_response(kb_response)
    elif intent_name == "Sleep":
        return form_sleep_intent_response(kb_response)
    elif intent_name == "Stay healthy":
        return form_stay_healthy_intent_response(kb_response)
    elif intent_name == "Stay safe":
        return form_stay_safe_intent_response(kb_response)
    elif intent_name == "Connect":
        return form_connect_intent_response(kb_response)
    elif intent_name == "Respect":
        return form_respect_intent_response(kb_response)