import spacy
from spacy.util import is_package
from spacy_cleaner import processing, Cleaner

def get_spacy_model(model_name="en_core_web_md"):
    """
    Ensure the SpaCy model is installed and return the loaded model.
    If the model is not installed, it is downloaded and installed.
    """
    try:
        # Check if the model is already installed
        if not is_package(model_name):
            print(f"Model '{model_name}' not found. Downloading...")
            from spacy.cli import download
            download(model_name)
        return spacy.load(model_name)
    except Exception as e:
        print(f"Error loading SpaCy model '{model_name}': {e}")
        raise

def clean_words(group):
    '''
    Function used to clean surrounding words of URL
    '''
    nlp = get_spacy_model('en_core_web_md')  # Automatically ensure the model is installed

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
    for i, (first, _) in enumerate(group):  # Put the words back in with their original URLs
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
    nlp = get_spacy_model('en_core_web_md')  # Automatically ensure the model is installed

    # Calculate similarities
    base_token = nlp(base_word)
    doc = nlp(words[1])

    to_return = []
    for token in doc:
        if token and token.vector_norm:  # Checks to make sure all of the tokens can be handled
            to_return.append(base_token.similarity(token))

    return words[0], to_return
