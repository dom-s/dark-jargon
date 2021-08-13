import os
import pandas as pd
import pickle as pkl
import re
from datetime import datetime
from typing import Sequence
from collections import Counter
from nltk import word_tokenize
from tqdm import tqdm
from db_handler import DBHandler
from utils import clean_str, get_dark_term_list
from yaml import safe_load

CONFIG = 'config.yaml'

DATE_REGEX = {
    'hackforums': re.compile(r'\(\d\d-\d\d-\d\d\d\d \d\d:\d\d (?:AM|PM)\)', re.IGNORECASE),
    'silkroad': re.compile(r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December) \d\d, \d\d\d\d, \d\d:\d\d (?:AM|PM)', re.IGNORECASE)
}
DATE_STR = {
    'hackforums': '(%m-%d-%Y %I:%M %p)',
    'silkroad': '%B %d, %Y, %I:%M %p'
}


def count_occurrences(timestamps: Sequence[datetime], texts: Sequence[str], term: str, timestamp_counter: Counter):
    for timestamp, text in zip(timestamps, texts):
        if timestamp is None:
            continue
        count_term = Counter(word_tokenize(text))[term]
        if count_term > 0:
            # only add timestamps that contain word occurrence
            timestamp_counter[timestamp] += count_term


def parse_comments(sents: Sequence[str], table_name):
    timestamps = [None]
    texts = []

    text = []
    for sent in sents:
        sent = clean_str(sent)
        date_strings = DATE_REGEX[table_name].findall(sent)
        if len(date_strings) == 0:
            text.append(sent)
        else:
            for date_string in date_strings:
                # print(date_string)
                split = sent.split(date_string)
                text.append(split[0])
                if len(split) > 1:
                    texts.append(' '.join(text))
                    text = []
                    sent = split[1]
                timestamps.append(datetime.strptime(date_string, DATE_STR[table_name]))
            text.append(sent)
    texts.append(' '.join(text))

    if len(timestamps) > 1:
        # approximate the first text to be written around the time of the first comment.
        timestamps[0] = min(timestamps[1:])

    return timestamps, texts


def extract_timestamps_for_db(db_handler: DBHandler, terms: Sequence[str]):
    term_to_timestamp = {}
    for term in tqdm(terms, desc=db_handler.table_name):
        timestamp_counter = Counter()
        if db_handler.table_name == 'darkode':
            comments, timestamps = db_handler.fetch_comments(term)
            count_occurrences(timestamps, comments, term, timestamp_counter)
        else:
            comments, _ = db_handler.fetch_comments(term)
            for comment in comments:
                timestamps, texts = parse_comments(comment, db_handler.table_name)
                count_occurrences(timestamps, texts, term, timestamp_counter)
        term_to_timestamp[term] = pd.Series(
            list(timestamp_counter.values()), list(timestamp_counter.keys()))
    return term_to_timestamp


def extract_timestamps(config: dict, dark_terms: Sequence[str]):
    timestamps = {}
    db_names = config['data']['db_names'][:3]
    for db_name in db_names:
        db_handler = DBHandler(config['data']['db_dir'], db_name)
        table_name = db_handler.table_name
        timestamps[table_name] = extract_timestamps_for_db(db_handler, dark_terms)
        total = timestamps.get('total', {})
        for dark_term in dark_terms:
            if dark_term not in total:
                series = timestamps[table_name][dark_term]
            else:
                series1 = timestamps['total'][dark_term]
                series2 = timestamps[table_name][dark_term]
                series = (series1+series2).fillna(series2).fillna(series1)
            total[dark_term] = series
        timestamps['total'] = total
        print('writing timestamps for {}'.format(db_name))
        pkl.dump(timestamps, open(dict_out, 'wb'))


if __name__ == '__main__':
    config = safe_load(open(CONFIG))
    resource_dir = config['data']['resource_dir']
    dark_term_csv = config['data']['dark_term_csv']
    dark_terms = get_dark_term_list(config)

    dict_out = os.path.join(resource_dir, config['timestamps']['dict_out'])
    extract_timestamps(config, dark_terms)
