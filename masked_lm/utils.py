import os
import pandas as pd
from nltk import word_tokenize
from typing import List, Tuple, Union


def clean_str(s: str) -> str:
    s = s.lower()
    for pattern in ['\\n', '\\r', '\\t', '\n', '\r', '\t']:
        s = s.replace(pattern, '')
    s.strip()
    return s


def word_window(sequence: str, target: str, size: int) -> Union[Tuple[List[str], List[str]], None]:
    """
    Retrieves word windows of 'size' to the left and 'size' to the right.
    If size == 0: Take the entire sequence as window
    """
    assert size >= 0
    tokens = word_tokenize(sequence.lower())
    if target not in tokens:
        return None
    else:
        target_idx = tokens.index(target)
        left_idx = max(target_idx-size, 0) if size > 0 else 0
        right_idx = target_idx+size+1 if size > 0 else len(tokens)
        return tokens[left_idx:target_idx], tokens[target_idx+1:right_idx]


def get_dark_term_list(config: dict) -> List[str]:
    input_dir = config['data']['resource_dir']
    dark_term_csv = config['data']['dark_term_csv']

    dark_terms = set(pd.read_csv(os.path.join(input_dir, dark_term_csv))['dark term'])

    for kl_div_file in config['data']['kl_div_files']:
        dark_terms.update(set(pd.read_csv(os.path.join(input_dir, kl_div_file))['dark_word']))

    return list(dark_terms)
