import torch
from typing import List, Union
from transformers import BertTokenizer, BertForMaskedLM


class WordPredictModel:
    def __init__(self, model_name: str, cuda: bool = True):
        self.tokenizer = BertTokenizer.from_pretrained(model_name)
        self.model = BertForMaskedLM.from_pretrained(model_name)
        self.model.eval()
        self.cuda = cuda
        if cuda:
            self.model.to('cuda')

    def most_likely(self, sequence: str, target: str, topk: int = 1) -> Union[List[str], None]:
        sequence = sequence.replace(target, '[MASK]', 1)

        text = '[CLS] ' + sequence + ' [SEP]'
        tokenized_text = self.tokenizer.tokenize(text)[:512]
        indexed_tokens = self.tokenizer.convert_tokens_to_ids(tokenized_text)

        # # Create the segments tensors.
        segments_ids = [0] * len(tokenized_text)
        try:
            masked_index = tokenized_text.index('[MASK]')
        except ValueError as e:
            print(e)
            print(tokenized_text)
            return None

        # # Convert inputs to PyTorch tensors
        tokens_tensor = torch.tensor([indexed_tokens])
        segments_tensors = torch.tensor([segments_ids])
        if self.cuda:
            tokens_tensor = tokens_tensor.to('cuda')
            segments_tensors = segments_tensors.to('cuda')

        # # Predict all tokens
        with torch.no_grad():
            try:
                predictions = self.model(tokens_tensor, segments_tensors)
            except:
                print('text = {}\n' 
                      'tokenized_text = {}\n'
                      'indexed_tokens = {}\n'
                      'segement_ids = {}'.format(
                    text, tokenized_text, indexed_tokens, segments_ids))

        idxs = torch.topk(predictions[0][0][masked_index], k=topk)[1]
        word_predict = self.tokenizer.convert_ids_to_tokens(idxs.tolist())
        return word_predict
