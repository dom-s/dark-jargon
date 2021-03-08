import pandas as pd
from utils.db_handler import DarkTermDB


def write_csv_to_db(csv_file, dark_term_db):
    df = pd.read_csv(csv_file, usecols=["dark term", "source", "definition", "definition source"])
    db = DarkTermDB(dark_term_db)
    for dark_term, source, definition, definition_source in df.values.tolist():
        db.insert_verified(dark_term, source, definition, definition_source)
