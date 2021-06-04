import numpy as np


def generate_batch_dataset(batch_size, unigram_dark, unigram_clean):
    dataset = []
    count = 0
    batch = []
    for dist_dark in unigram_dark:
        batch.append((dist_dark, unigram_clean))
        count += 1
        if count % batch_size == 0:
            dataset.append(batch)
            batch = []
    dataset.append(batch)
    return dataset


def reduce_results(results, vocab_size):
    distance = np.empty((vocab_size, vocab_size))
    row = 0
    for result in results:
        for distances in result:
            for col, val in enumerate(distances):
                distance[row, col] = val
            row += 1
    return distance
