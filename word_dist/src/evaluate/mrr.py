import argparse
import os
import logging
import pandas as pd
from datetime import datetime

from word_dist.src.utils.env import ROOT_DIR

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

parser = argparse.ArgumentParser(description='Create KL-Divergence Ranking Output')
parser.add_argument('--csv_path', type=str, required=True, help='folder name of distribution.py output')
args = parser.parse_args()

csv_path = args.csv_path

fout = open(f'{csv_path}/experiment-{datetime.now().isoformat()}.txt', 'w')

if __name__ == '__main__':
    fout.write('-' * 80 + '\n')
    fout.write(f'calculating for model: {csv_path}\n')

    for f in os.listdir(csv_path):
        if f.split('.')[-1] != 'csv':
            continue
        df = pd.read_csv(os.path.join(csv_path, f), usecols=['dark_word', 'mrr'])
        df_dash = df[df['dark_word'].apply(lambda x: isinstance(x, str) and x.startswith('_'))]

        fout.write(f'{len(df_dash)}\n')
        fout.write(f'Results for: {f}\n')
        fout.write(f"avg MRR: {df.mean(axis=0)['mrr']}\n")
        fout.write(f"avg MRR dashed: {df_dash.mean(axis=0)['mrr']}\n")

    logging.info(f'output written to: {fout.name}')
