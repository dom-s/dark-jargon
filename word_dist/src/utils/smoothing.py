def dirichlet_smoothing(unigram_doc, unigram_corpus, mu):
    vocab_size = unigram_doc.shape[0]
    nominator = unigram_doc + mu * (unigram_corpus / sum(unigram_corpus))
    denominator = unigram_doc.sum(axis=1).reshape((vocab_size, 1)) + mu
    return nominator / denominator


def laplace_smoothing(unigram, alpha):
    vocab_size = unigram.shape[0]
    unigram += alpha
    denominator = unigram.sum(axis=1).reshape((vocab_size, 1))
    return unigram / denominator
