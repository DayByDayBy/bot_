from api_etc import word_selection
from api_etc.api_handler import post_reply, get_posts
import random

def compose_reply(word):

    variations = {
        0: 'define ',
        1: 'first define ',
        2: 'well, how do you define ',
        3: 'how are you defining ',
        4: 'that depends on your definition of '
    }
    rando = random.choice(list(variations.keys()))
    return variations[rando] +f'"{word}"'


def main():
    api = None
    posts = get_posts(api)
    for post in posts:
        word = word_selection(post['text'])
        
        if word:
            reply = compose_reply(word)
            post_reply(api, post['id'], reply)
    
if __name__ == "__main__":
    main() 

