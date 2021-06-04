import os
import argparse
import csv
import numpy as np
import pandas as pd
import logging

from scipy.spatial.distance import jensenshannon
from scipy.stats import entropy
from itertools import chain
from tqdm import tqdm
from multiprocessing.pool import Pool
from gensim.corpora.dictionary import Dictionary
from smart_open import open

from word_dist.src.utils.preprocess import get_neighbor_unigram, filter_dict
from word_dist.src.utils.smoothing import dirichlet_smoothing, laplace_smoothing
from word_dist.src.utils.multiprocessing import generate_batch_dataset, reduce_results
from word_dist.src.utils.env import ROOT_DIR

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

parser = argparse.ArgumentParser(description='Word Distribution - Iterative Method')
parser.add_argument('--dataset', type=str, default='clean_clean', help='dataset name')
parser.add_argument('--dark_file', type=str, default='dark.txt', help='dark file name from which you want to calculate word distribution')
parser.add_argument('--clean_file', type=str, default='clean.txt', help='clean file name from which you want to calculate word distribution')
parser.add_argument('--num_neighbors', type=int, default=10, help='the number of left/right neighbors sampled for each neighbor')
parser.add_argument('--vocab_size', type=int, default=10000, help='how many most common/random word you want')
parser.add_argument('--alpha', type=float, default=1, help='laplace smoothing factor')
parser.add_argument('--mu', type=int, default=2000, help='dirichlet smoothing factor')
parser.add_argument('--smoothing', type=str, default='laplace', help='smoothing method to use, choose from: "laplace", "dirichlet"')
parser.add_argument('--percent_replace', type=float, default=0.05, help='percent of words you want to replace in clean text to mimic dark text (for example: 0.05 = 5%)')
parser.add_argument('--threshold', type=float, default=0.95, help='threshold for the iterative algorithm, it will stop after average MRR goes above this value')
parser.add_argument('--min_iterations', type=int, default=5, help='threshold for the iterative algorithm, it will stop after at least min_iterations')
parser.add_argument('--max_iterations', type=int, default=10, help='threshold for the iterative algorithm, it will stop after at most max_iterations')
parser.add_argument('--mrr_threshold', type=float, default=0.5, help='threshold for mrr. Words with mrr below this value will be filtered out during the iteration. ')
parser.add_argument('--topN', type=int, default=25, help='number of clean words in the ranking list for each dark word')
parser.add_argument('--batch_size', type=int, default=100, help='batch size for multiprocessing')
args = parser.parse_args()


def calc_distance(data):
    distances = []
    for dist_dark, unigram_clean in data:
        row = []
        for col, dist_clean in enumerate(unigram_clean):
            row.append(distance_fcn(dist_dark, dist_clean))
        distances.append(row)
    return distances


def replace_words(text, word_dict):
    for line in text:
        for i, word in enumerate(line):
            if word in word_dict:
                line[i] = word_dict[word]
    return text


def calculate_mrr(f):
    df = pd.read_csv(f, usecols=['mrr'])
    return df.mean(axis=0)['mrr']


def get_dark_words_prev(f):
    df = pd.read_csv(f, usecols=['dark_word', 'mrr'])
    return df[df['mrr'] >= args.mrr_threshold]['dark_word'].tolist()


def read_from_last_iter(output_dir):
    dirs = [i for i in os.listdir(output_dir) if i.startswith('iter')]
    if len(dirs) < 2:
        return 1, 0
    prev_dir = sorted(dirs)[-1]
    mrr = calculate_mrr(os.path.join(output_dir, prev_dir, 'ranking_list.csv'))
    next_iter = int(prev_dir.split('_')[1]) + 1
    return next_iter, mrr


def generate_ranking_list(distance, f_out):
    header, results = ['dark_word', 'dark_word_id', 'mrr'], []
    topN = args.topN
    for i in range(topN):
        header.extend(['clean_word_{}'.format(i), 'clean_word_{}_id'.format(i), 'clean_word_{}_kl'.format(i)])

    results.append(header)

    for i, row in enumerate(tqdm(distance)):
        token = dictionary[i]
        sort_ids = np.argsort(row)
        if token.startswith('_'):
            word_index = dictionary.token2id[token[1:]]
            mrr = 1.0 / (list(sort_ids).index(word_index) + 1)
        else:
            mrr = 1.0 / (list(sort_ids).index(i) + 1)
        sort_ids = sort_ids[:topN]
        sort_words = [dictionary[wid] for wid in sort_ids]
        sort_kldiv = [distance[i, wid] for wid in sort_ids]
        row_out = [token, i, mrr]
        for j in range(len(sort_ids)):
            row_out.extend([sort_words[j], sort_ids[j], sort_kldiv[j]])
        results.append(row_out)

    results = [results[0]] + sorted(results[1:], key=lambda x: x[2], reverse=True)
    wrtr = csv.writer(open(f_out, 'w'))
    wrtr.writerows(results)


if __name__ == '__main__':
    data_path = os.path.join(ROOT_DIR, "data", args.dataset)
    clean_file = os.path.join(data_path, args.clean_file)
    dark_file = os.path.join(data_path, args.dark_file)

    logging.info('loading text...')
    with open(clean_file) as f1, open(dark_file) as f2:
        clean_text = [line.split() for line in f1.readlines()]
        dark_text = [line.split() for line in f2.readlines()]

    param_dir = 'alpha_{}/'.format(args.alpha) if args.smoothing == 'laplace' else 'mu_{}/'.format(args.mu)
    output_dir = os.path.join(data_path, 'iterative', args.smoothing, param_dir)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    curr_iter, avg_mrr = read_from_last_iter(output_dir)

    while (avg_mrr < args.threshold or curr_iter <= args.min_iterations) and curr_iter <= args.max_iterations:
        curr_dir, prev_dir = os.path.join(output_dir, f'iter_{curr_iter}'), os.path.join(output_dir, f'iter_{curr_iter-1}')
        if not os.path.exists(curr_dir):
            os.mkdir(curr_dir)

        logging.info('computing for ' + str(curr_iter) + '...')

        file_unigram_dark = os.path.join(curr_dir, 'unigram_dark.npy')
        file_unigram_clean = os.path.join(curr_dir, 'unigram_clean.npy')
        file_unigram_dark_all = os.path.join(curr_dir, 'unigram_dark_all.npy')
        file_unigram_clean_all = os.path.join(curr_dir, 'unigram_clean_all.npy')

        if args.smoothing == 'laplace':
            output_file_dist = os.path.join(curr_dir, f'distance_{args.smoothing}_{args.alpha}')
        elif args.smoothing == 'dirichlet':
            output_file_dist = os.path.join(curr_dir, f'distance_{args.smoothing}_{args.mu}')
        else:
            output_file_dist = os.path.join(curr_dir, 'distance_js')

        logging.info('creating the dictionary for ' + str(curr_iter) + '...')

        if curr_iter == 1:
            dict_file = os.path.join(curr_dir, 'dict.model')
            if os.path.exists(dict_file):
                logging.info(f'loading dictionary file from: {dict_file}')
                dictionary = Dictionary.load(dict_file)
            else:
                dictionary = Dictionary(dark_text)
                dictionary.add_documents(clean_text)

                word_dict = {word[1:]: word for word in dictionary.itervalues() if word.startswith('_')}
                _dict = Dictionary([[word] for word in word_dict.keys()])
                dictionary.merge_with(_dict)

                dictionary = filter_dict(args.vocab_size, dictionary, chain(word_dict.values(), word_dict.keys()))
                dictionary.save(dict_file)

        else:
            dict_file_prev = os.path.join(prev_dir, 'dict.model')
            dict_file = os.path.join(curr_dir, 'dict.model')
            mrr_file = os.path.join(prev_dir, 'ranking_list.csv')

            dictionary = Dictionary.load(dict_file_prev)
            word_dict = {word[1:]: word for word in dictionary.itervalues() if word.startswith('_')}
            words = get_dark_words_prev(mrr_file)

            dictionary.filter_extremes(no_below=len(dark_text)+1, keep_tokens=chain(words, word_dict.values(), word_dict.keys())) # Do this primarily because docID may be useful
            dictionary.save(dict_file)

        logging.info('dictionary created')

        logging.info('building neighbor unigrams for ' + str(curr_iter) + '...')

        if os.path.exists(file_unigram_dark) and os.path.exists(file_unigram_dark_all):
            logging.info('loading precalculated dark unigram counts...')
            unigram_dark = np.load(file_unigram_dark)
            unigram_dark_all = np.load(file_unigram_dark_all)
        else:
            unigram_dark, unigram_dark_all = get_neighbor_unigram(dictionary, dark_text, args.num_neighbors)
            np.save(file_unigram_dark, unigram_dark)
            np.save(file_unigram_dark_all, unigram_dark_all)

        if os.path.exists(file_unigram_clean) and os.path.exists(file_unigram_clean_all):
            logging.info('loading precalculated clean unigram counts...')
            unigram_clean = np.load(file_unigram_clean)
            unigram_clean_all = np.load(file_unigram_clean_all)
        else:
            unigram_clean, unigram_clean_all = get_neighbor_unigram(dictionary, clean_text, args.num_neighbors)
            np.save(file_unigram_clean, unigram_clean)
            np.save(file_unigram_clean_all, unigram_clean_all)

        logging.info('neighbor unigrams built for ' + str(curr_iter) + '...')


        if args.smoothing == 'laplace':
            unigram_dark = laplace_smoothing(unigram_dark, args.alpha)
            unigram_clean = laplace_smoothing(unigram_clean, args.alpha)
            distance_fcn = entropy
            distance_fcn_name = 'kl'
        elif args.smoothing == 'dirichlet':
            unigram_dark = dirichlet_smoothing(unigram_dark, unigram_dark_all, args.mu)
            unigram_clean = dirichlet_smoothing(unigram_clean, unigram_clean_all, args.mu)
            distance_fcn = entropy
            distance_fcn_name = 'kl'
        else:
            distance_fcn = jensenshannon
            distance_fcn_name = 'js'

        if os.path.exists(output_file_dist):
            logging.info(f'loading distance matrix from: {output_file_dist}')
            distance = np.load(output_file_dist)
        else:
            logging.info(f'calculating distance of two distributions using {distance_fcn_name}-divergence(clean-clean) for iter: ' + str(curr_iter) + '...')
            dataset = generate_batch_dataset(args.batch_size, unigram_dark, unigram_clean)

            with Pool() as pool:
                results = list(tqdm(pool.imap(calc_distance, dataset), total=len(dataset)))

            logging.info(f'Batches processed: {len(results)}')

            distance = reduce_results(results, vocab_size=len(dictionary))
            np.save(output_file_dist, distance)
            logging.info('distance calculated')

        logging.info('calculating ranking list for ' + str(curr_iter) + '...')
        f_out = os.path.join(curr_dir, 'ranking_list.csv')
        generate_ranking_list(distance, f_out)

        avg_mrr = calculate_mrr(f_out)
        logging.info('Iteration ' + str(curr_iter) + ' done!')
        curr_iter += 1
        logging.info('-'*100)
