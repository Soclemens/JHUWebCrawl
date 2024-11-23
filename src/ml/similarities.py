import spacy
from spacy_cleaner import processing, Cleaner

def calculate_similarities(base_word, words):
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
    nlp = spacy.load('en_core_web_sm')
    cleaner = Cleaner(
        nlp,
        processing.remove_stopword_token,
        processing.remove_punctuation_token,
        processing.remove_email_token,
        processing.replace_email_token,
        processing.replace_url_token,
        processing.mutate_lemma_token,
    )
    words = cleaner.clean([words])[0]
    # Calculate similarities
    base_token = nlp(base_word)
    doc = nlp(words)
    # filtered_tokens =  [token for token in doc if not token.is_stop]  # removes stop words like  "the", and "is". Should create a more accurate similarity score
    similarities = {}
    for token in doc:
        similarities[token] = base_token.similarity(token)
    
    return similarities
