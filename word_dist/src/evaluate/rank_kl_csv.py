import argparse
import csv
import os
import logging
import numpy as np
from gensim.corpora.dictionary import Dictionary
from tqdm import tqdm

from word_dist.src.utils.env import ROOT_DIR
from word_dist.src.utils.preprocess import filter_dict
from word_dist.src.commands.distribution import get_keep_tokens

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

parser = argparse.ArgumentParser(description='Create KL-Divergence Ranking Output')
parser.add_argument('--dataset', type=str, default='clean_clean', help='dataset name')
parser.add_argument('--input_path', type=str, default='distribution', help='folder name of distribution.py output')
parser.add_argument('--dict_keep_n', type=int, default=10000, help='number of words to keep after dict pruning')
parser.add_argument('--top_n', type=int, default=25, help='number of highest-ranked items in output')
args = parser.parse_args()


data_dir = os.path.join(ROOT_DIR, 'data/', args.dataset)
input_dir = os.path.join(data_dir, args.input_path, args.dataset)


def load_dictionary(dict_dir):
    f_dict = os.path.join(dict_dir, 'dict_all.model')
    dictionary = Dictionary.load(f_dict)
    dictionary = filter_dict(args.dict_keep_n, dictionary, get_keep_tokens(dictionary))
    return dictionary


def write_to_file(dictionary, distance, f_out, topN):
    header = ['dark_word', 'dark_word_id', 'mrr']
    for i in range(topN):
        header.extend(['clean_word_{}'.format(i), 'clean_word_{}_id'.format(i), 'clean_word_{}_kl'.format(i)])

    results = [header]

    for i, col in enumerate(tqdm(distance)):
        token = dictionary[i]
        if token.startswith('_') and token[1:] in dictionary.token2id:
            # make sure to count mrr correctly for simulated dark words
            token_id = dictionary.token2id[token[1:]]
        else:
            token_id = i
        sort_ids = np.argsort(col)
        mrr = 1.0 / (list(sort_ids).index(token_id) + 1)
        sort_ids = sort_ids[:topN]
        sort_words = [dictionary[wid] for wid in sort_ids]
        sort_kldiv = [distance[i, wid] for wid in sort_ids]
        row_out = [token, i, mrr]
        for j in range(len(sort_ids)):
            row_out.extend([sort_words[j], sort_ids[j], sort_kldiv[j]])
        results.append(row_out)

    results = [results[0]] + sorted(results[1:], key=lambda x: x[2], reverse=True)

    with open(f_out, 'w', newline='') as csv_file:
        wrtr = csv.writer(csv_file)
        wrtr.writerows(results)


def generate_csv_output(input_dir, dictionary):
        f_in = [x for x in os.listdir(input_dir) if x.startswith('distance')]
        for f in f_in:
            distance = np.load(os.path.join(input_dir, f))
            f_out = f.replace('distance', 'rank').replace('npy', 'csv')
            logging.info('generating csv_ranking for: %s', f_out)
            csv_out_dir = os.path.join(input_dir, 'csv_output')
            if not os.path.exists(csv_out_dir):
                os.mkdir(csv_out_dir)
            f_out = os.path.join(csv_out_dir, f_out)
            write_to_file(dictionary, distance, f_out, args.top_n)


if __name__ == '__main__':
    logging.info('loading dictionaries...')
    dictionary = load_dictionary(data_dir)

    logging.info('writing csv output...')
    generate_csv_output(input_dir, dictionary)
