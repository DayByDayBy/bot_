from words_etc import word_selection
from api_etc.api_handler import post_reply, get_posts
import random

def compose_reply(word):
    
    rando = random.choice(0,5)
    
    variations = {
        0: 'define ',
        1: 'first define ',
        2: 'well, how do you define ',
        3: 'how are you defining ',
        4: 'that depends on your definition of '
    }
    return variations[rando] + word
    
 