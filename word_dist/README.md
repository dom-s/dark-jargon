# Word Distribution Modeling for Dark Jargon Interpretation

This folder contains all code related to the Word Distribution Modeling Method from Seyler et al., ECIR 2021.

## Datasets

The required datasets can be downloaded here: https://uofi.box.com/s/lts9heh7x47a7r1p502lzz4x7lk2t0k5

After download:

- extract files: `tar -xf word_dist-data.tar.gz`
- copy `data` folder: `cp -r data <repository-root>/word_dist/`


## Run Experiment Scripts

To reproduce the experiments for language model smoothing execute `bash word_dist/script/run_smoothing-clean_clean.sh`. These results were not included in the ECIR work but can be found in the Ph.D. thesis.

To reproduce the iterative results **TODO**


## Description of components

### One-step

This is the rough outline of steps that are taken during the "one-step" computation of the word distribution experiments. 

- `word_dist/src/commands/distribution.py` create the word distributions and calculating distance
- `word_dist/src/evaluate/rank_kl_csv.py` create the csv ranking file
- `word_dist/src/evaluate/mrr.py` get the Mean Reciprocal Rank (MRR) results using the csv file output


### Iterative

- `word_dist/src/commands/iterative.py` iteratively create the word distributions and calculating distance
- `word_dist/src/evaluate/mrr.py` get the Mean Reciprocal Rank (MRR) results using the csv file output


## Research Usage

If you use our work in your research please cite:

```
@inproceedings{seyler2021towards,
  title={Towards Dark Jargon Interpretation in Underground Forums},
  author={Seyler, Dominic and Liu, Wei and Wang, XiaoFeng and Zhai, ChengXiang},
  booktitle={European Conference on Information Retrieval},
  year={2021}
}
```