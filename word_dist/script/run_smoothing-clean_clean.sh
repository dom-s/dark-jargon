#!/bin/bash

# laplace smoothing
python -m word_dist.src.commands.distribution --dataset clean_clean --alpha 0.1 --smoothing laplace
python -m word_dist.src.commands.distribution --dataset clean_clean --alpha 1.0 --smoothing laplace
python -m word_dist.src.commands.distribution --dataset clean_clean --alpha 2.0 --smoothing laplace
python -m word_dist.src.commands.distribution --dataset clean_clean --alpha 10.0 --smoothing laplace
python -m word_dist.src.commands.distribution --dataset clean_clean --alpha 15.0 --smoothing laplace
python -m word_dist.src.commands.distribution --dataset clean_clean --alpha 20.0 --smoothing laplace
python -m word_dist.src.commands.distribution --dataset clean_clean --alpha 30.0 --smoothing laplace

# rank results and generate csv files
python -m word_dist.src.evaluate.rank_kl_csv

# evaluate mean reciprocal rank
python -m word_dist.src.evaluate.mrr --csv_path word_dist/data/clean_clean/distribution/clean_clean/csv_output/