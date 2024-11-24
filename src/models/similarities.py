import spacy
from spacy_cleaner import processing, Cleaner

def clean_words(group):
    '''
    Function used to clean surrounding words of URL
    '''
    nlp = spacy.load('en_core_web_md')

    cleaner = Cleaner(
        nlp,
        processing.remove_stopword_token,
        processing.remove_punctuation_token,
        processing.remove_email_token,
        processing.replace_email_token,
        processing.replace_url_token,
        processing.mutate_lemma_token,
    )

    words = cleaner.clean([t[1] for t in group])  # Clean all of the surrounding words
    result = []
    for i, (first, _) in enumerate(group):  # Put the words back in with their original URLS
        result.append((first, words[i]))
    return result

def calculate_similarities(words, base_word):
    '''
    Function that takes in a target word and string and returns the 
    similarity score for each token in the string

    # Example usage
    base_word = "king"
    words = "Apple is looking at buying U.K. startup for $1 billion"
    similarities = calculate_similarities(base_word, words)

    print(f"Similarities to '{base_word}':")
    for word, score in similarities.items():
        print(f"{word}: {score:.2f}")
    '''
    # Spacy stuff
    nlp = spacy.load('en_core_web_md')  # loads the pre-made database 

    # Calculate similarities
    base_token = nlp(base_word)
    doc = nlp(words[1])

    to_return = []
    for token in doc:
        if token and token.vector_norm:  # Checks to make sure all of the tokens can be handled
            to_return.append(base_token.similarity(token))

    return words[0], to_return
