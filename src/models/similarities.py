import spacy
from spacy.util import is_package
from spacy_cleaner import processing, Cleaner

def get_spacy_model(model_name="en_core_web_md"):
    try:
        if not is_package(model_name):
            print(f"Model '{model_name}' not found. Downloading...")
            from spacy.cli import download
            download(model_name)
        return spacy.load(model_name)
    except Exception as e:
        print(f"Error loading SpaCy model '{model_name}': {e}")
        raise

def clean_words(group):
    if not group or not isinstance(group, list):
        print("Invalid input to clean_words: Expected a list of tuples.")
        return []

    nlp = get_spacy_model('en_core_web_md')

    cleaner = Cleaner(
        nlp,
        processing.remove_stopword_token,
        processing.remove_punctuation_token,
        processing.remove_email_token,
        processing.replace_email_token,
        processing.replace_url_token,
        processing.mutate_lemma_token,
    )

    try:
        words = cleaner.clean([t[1] for t in group if len(t) > 1])
    except Exception as e:
        print(f"Error during cleaning words: {e}")
        return []

    result = []
    for i, (first, _) in enumerate(group):
        if i < len(words):
            result.append((first, words[i]))
        else:
            print(f"Skipping tuple with missing text: {group[i]}")

    return result

def calculate_similarities(words, base_word):
    if not words or len(words) < 2:
        print(f"Invalid input to calculate_similarities: {words}")
        return words[0] if words else None, []

    try:
        nlp = get_spacy_model('en_core_web_md')
        base_token = nlp(base_word)
        doc = nlp(words[1])

        to_return = []
        for token in doc:
            if token and token.vector_norm:
                to_return.append(base_token.similarity(token))

        return words[0], to_return
    except Exception as e:
        print(f"Error in calculate_similarities for {words}: {e}")
        return words[0], []
