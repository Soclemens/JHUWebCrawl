'''
10/6/2024
Model for ingesting strings and determining level of "context" matching. 
'''

def context_score(input_string: str, key_term: str) -> float:
    '''
    Function that determines how much context an input string has for a given term.
    Possible solution would be N-gram Analysis.

    Input:
        input_string (str): An input string
        key_term (str): The term we wish to see if the input has relative context against
    Output:
        _ (float): A score *Still needs to be decided how this is calculated
    Example:
        input_string = "shohei ohtani hit his 50th homerun of the season"
        key_term = "baseball"
        output = high score
    '''
    pass