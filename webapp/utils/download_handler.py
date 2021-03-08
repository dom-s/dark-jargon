import os
import pandas as pd
from datetime import datetime
from webapp.utils.backend import get_collab_for_file_dump, get_verified
from webapp.utils.db_handler import DarkTermDB

TMP_FOLDER = 'webapp/static/download/'
FILE_TEMPLATE = 'dark-terms_{}_{}.csv'


def get_file_path(dark_term_type: str, dark_term_db: DarkTermDB):
    if not os.path.exists(TMP_FOLDER):
        os.mkdir(TMP_FOLDER)

    if dark_term_type == 'verified':
        header, body = get_verified(dark_term_db)
    else:
        print('else')
        header, body = get_collab_for_file_dump(dark_term_db)

    df = pd.DataFrame(data=body, columns=header)
    timestamp = int(datetime.now().timestamp())
    f_out = os.path.join(TMP_FOLDER, FILE_TEMPLATE.format(dark_term_type, timestamp))
    df.to_csv(f_out)
    return f_out
