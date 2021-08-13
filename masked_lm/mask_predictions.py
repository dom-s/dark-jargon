import os
import pickle as pkl
from collections import Counter, defaultdict, namedtuple
from nltk import sent_tokenize
from tqdm import tqdm
from typing import List, DefaultDict, Tuple, Union, Dict
from yaml import safe_load

from db_handler import DBHandler
from model_predict import WordPredictModel
from utils import clean_str, word_window, get_dark_term_list

CONFIG = 'config.yaml'

WordWindow = namedtuple('WordWindow', ['target', 'left', 'right'])


def _fetch_word_windows(dark_terms: List[str], hdlr: DBHandler, window_size: int) -> Union[List[WordWindow], list]:
    word_windows = []

    for dark_term in tqdm(dark_terms, desc='dark_terms'):
        result, _ = hdlr.fetch_comments(dark_term)
        for comments in result:
            for comment in sent_tokenize(comments):
                ww = word_window(clean_str(comment), dark_term, size=window_size//2)
                if ww:
                    left, right = ww
                    word_windows.append(WordWindow(dark_term, left, right))

    return word_windows


def _predict_masked_words(word_windows: List[WordWindow],
                          model: WordPredictModel,
                          top_k: int) -> DefaultDict[str, Counter]:
    counters = defaultdict(Counter)

    for target, left, right in tqdm(word_windows, desc='word_windows'):
        sequence = ' '.join(left + [target] + right)
        predictions = model.most_likely(sequence, target, top_k)
        if predictions:
            for i, prediction in enumerate(predictions):
                counters[target][prediction] += 1 / (i+1)

    return counters


def count_predictions(config: dict, db_name: str, dark_terms: List[str]) -> Tuple[List[WordWindow], DefaultDict[str, Counter]]:
    hdlr = DBHandler(config['data']['db_dir'], db_name)
    model = WordPredictModel(config['mask']['model_name'])

    word_windows = _fetch_word_windows(dark_terms, hdlr, config['mask']['window_size'])
    counters = _predict_masked_words(word_windows, model, config['mask']['top_k'])

    return word_windows, counters


def agg_totals(counters: Dict[str, DefaultDict[str, Counter]]) -> Dict[str, DefaultDict[str, Counter]]:
    totals = defaultdict(Counter)
    for db_name in counters.keys():
        for dark_term in counters[db_name].keys():
            for prediction, count in counters[db_name][dark_term].items():
                totals[dark_term][prediction] += count

    counters['total'] = totals
    return counters


def _create_or_load_counters(output_dir: str, f_out: str) -> Dict[str, DefaultDict[str, Counter]]:
    path_out = os.path.join(output_dir, f_out)
    if os.path.exists(path_out):
        counters = pkl.load(open(path_out, 'rb'))
    else:
        counters = {}

    return counters


def mask_predictions(config):
    config_data = config['data']
    config_mask = config['mask']
    dark_terms = get_dark_term_list(config)

    f_out = 'counters_all_{}_W-{}_K-{}.pkl'.format(config_mask['model_name'],
                                                   config_mask['window_size'],
                                                   config_mask['top_k'])

    counters = _create_or_load_counters(config_mask['output_dir'], f_out)

    for db_name in config_data['db_names']:
        print(db_name)
        if db_name in counters.keys():
            print('skipping...')
            continue
        _, counters[db_name] = count_predictions(config, db_name, dark_terms)
        print('saving counters...')
        pkl.dump(counters, open(os.path.join(config_mask['output_dir'], f_out), 'wb'))

    counters = agg_totals(counters)

    pkl.dump(counters, open(os.path.join(config_mask['output_dir'], f_out), 'wb'))


if __name__ == '__main__':
    mask_predictions(safe_load(open(CONFIG)))
