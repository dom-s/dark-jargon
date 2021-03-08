import os
import re
import numpy as np
import pandas as pd
import pickle as pkl
from collections import Counter
from nltk.corpus import stopwords
from operator import itemgetter
from scipy.special import softmax
from webapp.utils.db_handler import DarkTermDB

stop_words = set(stopwords.words('english'))


def get_verified(dark_term_db: DarkTermDB):
    """
    helper function to read verified data from db
    The first return value is the name of the columns as a 1-d list
    The second is the data as a 2-d list
    The table in the HTML will automatically expand
    """
    header = ['dark term', 'definition', 'definition source']
    body = dark_term_db.fetch_verified()
    return header, body


def get_collab(dark_term_db: DarkTermDB):
    header = ['dark term', 'definition', 'definition source', 'submitted by', '', '']
    body = dark_term_db.fetch_collab()
    return header, body


def get_collab_for_file_dump(dark_term_db: DarkTermDB):
    header = ['dark term', 'definition', 'definition source', 'submitted by', 'vote_valid', 'vote_invalid']
    body = dark_term_db.fetch_collab_for_file_dump()
    return header, body


def parse_series(series):
    idx = [ts.to_pydatetime().isoformat() for ts in list(series.index)]
    count = series.to_list()
    return list(zip(idx, count))


def get_usage_data(term: str, usage_data: dict):
    data_dict = {}
    for key in usage_data:
        if term in usage_data[key] and len(usage_data[key][term]) > 0:
            series = usage_data[key][term].resample('D').sum()
            data_dict[key] = parse_series(series)
    return data_dict


def _calculate_softmax(scores: list):
    scores = np.array(scores) * -1
    return np.log(softmax(scores))


def _kl_data_to_prob(f_kl: str):
    df = pd.read_csv(f_kl)
    key_word = [f'clean_word_{i}' for i in range(25)]
    key_kl = [f'clean_word_{i}_kl' for i in range(25)]
    probs = {}
    dark_terms = df['dark_word'].values.tolist()
    clean_words = df[key_word].values.tolist()
    kls = _calculate_softmax(df[key_kl].values.tolist())
    for dark_term, clean_word, kl in zip(dark_terms, clean_words, kls):
        probs[dark_term] = sorted([(cw, val) for cw, val in zip(clean_word, kl)], key=itemgetter(1), reverse=True)
    return probs


def get_kl_data(kl_dir: str, forum_names: list):
    kl_data = {}
    for forum_name in forum_names:
        kl_data[forum_name] = _kl_data_to_prob(os.path.join(kl_dir, f'{forum_name}-rank_laplace_1.0.csv'))
    return kl_data


def _filter_most_common(words: list, probs: list):
    filtered = []
    for word, prob in zip(words, probs):
        if word.isalpha() and word not in stop_words:
            filtered.append((word, prob))
    return filtered


def get_bert_data(f_data: str):
    bert_data = pkl.load(open(f_data, 'rb'))
    output = {}
    for key, counters in bert_data.items():
        forum_name = re.sub(r'_.+', '', key)
        forum_data = {}
        for term, counter in counters.items():
            words, counts = zip(*counter.most_common())
            probs = list(np.log(softmax(counts)))
            most_common = _filter_most_common(words, probs)
            if len(most_common):
                forum_data[term] = [(clean_word, prob) for clean_word, prob in most_common]
        output[forum_name] = forum_data
    return output
