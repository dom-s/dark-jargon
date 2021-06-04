#!/bin/bash

# run iterations
python -m word_dist.src.commands.iterative

# evaluate mrr
for dir in word_dist/data/clean_clean/iterative/laplace/alpha_1/* ; do
  python -m word_dist.src.evaluate.mrr --csv_path $dir
done

mkdir word_dist/data/clean_clean/iterative/laplace/alpha_1/results

cat word_dist/data/clean_clean/iterative/laplace/alpha_1/iter_*/experiment*.txt > word_dist/data/clean_clean/iterative/laplace/alpha_1/results/mrr.txt

echo "results stored in word_dist/data/clean_clean/iterative/laplace/alpha_1/results/mrr.txt"