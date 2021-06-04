import numpy as np
from tqdm import tqdm

from nltk.corpus import stopwords


def get_neighbor_unigram(vocab, text, n):
    # @param vocab: dictionary of the most frequent words.
    # @param text: text(list of lists) with each line(document) splitted to list
    # @param n: number of neighbors
    vocab_size = len(vocab)
    unigram = np.zeros((vocab_size, vocab_size))
    unigram_all = np.zeros(vocab_size)
    for doc in tqdm(text):
        for pos, word in enumerate(doc):
            if vocab.token2id.get(word, -1) == -1:
                continue
            left_pos = max(pos - n, 0)
            right_pos = min(pos + n + 1, len(doc))
            neighbors_idx = [x for x in vocab.doc2idx(doc[left_pos: pos] + doc[pos + 1: right_pos]) if x != -1]
            row_idx = vocab.token2id[word]
            unigram_all[row_idx] += 1
            for col_idx in neighbors_idx:
                unigram[row_idx, col_idx] += 1

    return unigram, unigram_all


def filter_dict(keep_n, dictionary, keep_tokens=None):
    bad_ids = [dictionary.token2id[stopword]
               for stopword in stopwords.words('english')
               if stopword in dictionary.token2id and stopword not in keep_tokens]
    dictionary.filter_tokens(bad_ids=bad_ids)
    dictionary.filter_extremes(keep_n=keep_n, keep_tokens=keep_tokens)
    return dictionary
