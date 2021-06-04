import os
import argparse
import numpy as np
import logging

from scipy.spatial.distance import jensenshannon
from scipy.stats import entropy
from tqdm import tqdm
from itertools import chain
from multiprocessing.pool import Pool
from gensim.corpora.dictionary import Dictionary
from smart_open import open

from word_dist.src.utils.preprocess import get_neighbor_unigram, filter_dict
from word_dist.src.utils.smoothing import dirichlet_smoothing, laplace_smoothing
from word_dist.src.utils.multiprocessing import generate_batch_dataset, reduce_results
from word_dist.src.utils.env import ROOT_DIR

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

parser = argparse.ArgumentParser(description='Word Distribution')
parser.add_argument('--dataset', type=str, default='clean_clean', help='dataset name')
parser.add_argument('--dark_file', type=str, default='dark.txt', help='dark file name from which you want to calculate word distribution')
parser.add_argument('--clean_file', type=str, default='clean.txt', help='clean file name from which you want to calculate word distribution')
parser.add_argument('--num_neighbors', type=int, default=10, help='the number of left/right neighbors sampled for each neighbor')
parser.add_argument('--vocab_size', type=int, default=10000, help='how many most common/random word you want')
parser.add_argument('--alpha', type=float, default=1.0, help='laplace smoothing factor')
parser.add_argument('--mu', type=int, default=2000, help='dirichlet smoothing factor')
parser.add_argument('--smoothing', type=str, default='', help='smoothing method to use, choose from: "laplace", "dirichlet"')
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


def get_keep_tokens(dictionary):
    sim_dark_term_mapping = {word[1:]: word for word in dictionary.itervalues() if word.startswith('_')}
    keep_tokens = list(chain(sim_dark_term_mapping.values(), sim_dark_term_mapping.keys()))
    return keep_tokens


if __name__ == '__main__':
    data_path = os.path.join(ROOT_DIR, "data", args.dataset)
    output_path = os.path.join(data_path, 'distribution', args.dataset)
    os.makedirs(output_path, exist_ok=True)

    data_dark_file = os.path.join(data_path, args.dark_file)
    data_clean_file = os.path.join(data_path, args.clean_file)
    
    if args.smoothing == 'laplace':
        output_file_dist = os.path.join(output_path, f'distance_{args.smoothing}_{args.alpha}')
    elif args.smoothing == 'dirichlet':
        output_file_dist = os.path.join(output_path, f'distance_{args.smoothing}_{args.mu}')
    else:
        output_file_dist = os.path.join(output_path, 'distance_js')

    dict_file = os.path.join(data_path, 'dict_all.model')

    file_unigram_dark = os.path.join(output_path, 'unigram_dark.npy')
    file_unigram_clean = os.path.join(output_path, 'unigram_clean.npy')
    file_unigram_dark_all = os.path.join(output_path, 'unigram_dark_all.npy')
    file_unigram_clean_all = os.path.join(output_path, 'unigram_clean_all.npy')

    if os.path.exists(dict_file) and os.path.exists(file_unigram_dark)\
            and os.path.exists(file_unigram_clean) and os.path.exists(file_unigram_dark_all) \
            and os.path.exists(file_unigram_clean_all):
        logging.info('loading precalculated results...')
        unigram_dark = np.load(file_unigram_dark)
        unigram_clean = np.load(file_unigram_clean)
        unigram_dark_all = np.load(file_unigram_dark_all)
        unigram_clean_all = np.load(file_unigram_clean_all)

        dictionary = Dictionary.load(dict_file)
        dictionary = filter_dict(args.vocab_size, dictionary, get_keep_tokens(dictionary))

    else:
        logging.info('no calculated files found, recomputing...')
        logging.info('loading files...')
        with open(data_dark_file, 'r') as f1, open(data_clean_file, 'r') as f2:
            logging.info('loading dark text...')
            dark_text = [line.split() for line in f1.readlines()]
            logging.info('loading clean text...')
            clean_text = [line.split() for line in f2.readlines()]
            logging.info('load file done')

        if os.path.exists(dict_file):
            dictionary = Dictionary.load(dict_file)
        else:
            logging.info('creating the dictionary...')
            dictionary = Dictionary(dark_text)
            dictionary.add_documents(clean_text)
            dictionary.save(dict_file)

        dictionary = filter_dict(args.vocab_size, dictionary, get_keep_tokens(dictionary))
        logging.info('dictionary created')

        logging.info('building neighbor unigrams...')

        if os.path.exists(file_unigram_dark) and os.path.exists(file_unigram_dark_all):
            unigram_dark = np.load(file_unigram_dark)
            unigram_dark_all = np.load(file_unigram_dark_all)
        else:
            unigram_dark, unigram_dark_all = get_neighbor_unigram(dictionary, dark_text, args.num_neighbors)
            np.save(file_unigram_dark, unigram_dark)
            np.save(file_unigram_dark_all, unigram_dark_all)

        if os.path.exists(file_unigram_clean) and os.path.exists(file_unigram_clean_all):
            unigram_clean = np.load(file_unigram_clean)
            unigram_clean_all = np.load(file_unigram_clean_all)
        else:
            unigram_clean, unigram_clean_all = get_neighbor_unigram(dictionary, clean_text, args.num_neighbors)
            np.save(file_unigram_clean, unigram_clean)
            np.save(file_unigram_clean_all, unigram_clean_all)

        logging.info('neighbor unigrams built')

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

    logging.info(f'calculating distance of two distributions using {distance_fcn_name}-divergence(dark-clean)')
    dataset = generate_batch_dataset(args.batch_size, unigram_dark, unigram_clean)

    with Pool() as pool:
        results = list(tqdm(pool.imap(calc_distance, dataset), total=len(dataset)))

    logging.info(f'Batches processed: {len(results)}')

    distance = reduce_results(results, vocab_size=len(dictionary))

    logging.info('distance calculated')
    np.save(output_file_dist, distance)
