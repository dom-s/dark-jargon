# Masked Language Modeling for Dark Jargon Interpretation

This folder contains code related to the masked langage modeling component from Seyler et al., SIGIR 2021.

## Masked Language Model Predictions

In order to perform masked language model predictions one can use `mask_predictions.py`. This will create a pickle file that stores the counts of the predicted tokens for each passed dark term. This is a dictionary of dictionaries, where on the top level the keys of each dictionary are the forum names (+ 'total' for aggregate counts). On the next level the keys are the dark terms, which map to the tokens that were predicted by the model and their counts.

## Extract Mention Timestamps

Running `extract_timestamps.py` will seach for mentions of dark terms in the underground forum and extract the timestamp of said mentions. Timestamps are stored as pandas.Series objects. 

## Description of components

- `config.yaml` the configuration file that specifies the paths and file names for input/output and additional hyper-parameters.
- `db_handler.py` helper class that handles database connections.
- `extract_timestamps.py` code for extracting timestamps of dark term mentions from forums.
- `mask_predictions.py` code for running the mask language modeling interpretation.
- `model_predict.py` helper class that encapsulates the MLM prediction model.
- `utils.py` utility functions.

## Datasets

The code requires a set of databases of dark forum communication traces. Please reach out to the authors, if you would like to obtain these databases.

## Research Usage

If you use our work in your research please cite:

```
@inproceedings{seyler2021darkjargonnet,
  title={DarkJargon.net: A Platform for Understanding Underground Conversation with Latent Meaning},
  author={Seyler, Dominic and Liu, Wei and Zhang, Yunan and Wang, XiaoFeng and Zhai, ChengXiang},
  booktitle={International ACM SIGIR Conference on Research and Development in Information Retrieval},
  year={2021}
}
```