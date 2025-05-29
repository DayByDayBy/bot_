import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import random

nltk.download('punkt')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')

def select_word(text):
    # tokenize!
    words = word_tokenize(text)

    # remove stopwords/non-alphabetics
    stop_words = set(stopwords.words('english'))
    words = [word for word in words if word.isalpha() and word not in stop_words]

    # select from nouns, verbs, adjectives, and adverbs
    tagged_words = nltk.pos_tag(words)
    selected_words = [word for word, pos in tagged_words if pos.startswith(('N', 'V', 'J', 'R'))]

    # a random word from the selected words
    return random.choice(selected_words) if selected_words else None
