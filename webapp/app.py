import pickle as pkl
from flask import Flask, render_template, request, send_file
from webapp.utils import backend, download_handler
from webapp.utils.db_handler import DarkTermDB, LogDB


def create_app():
    app = Flask(__name__)
    app.config.from_pyfile('config.py')
    app.secret_key = app.config["SECRET_KEY"]

    num_clean_terms = app.config["NUM_CLEAN_TERMS"]
    timestamp_data = pkl.load(open(app.config["DARK_TERM_TIMESTAMPS"], 'rb'))
    kl_data = backend.get_kl_data(app.config["DARK_TERM_KL_FOLDER"], app.config["DARK_FORUM_NAMES"])
    bert_data = backend.get_bert_data(app.config["DARK_TERM_BERT_MAPPING"])

    @app.route('/', methods=['GET'])
    def table():
        log_db = LogDB(app.config['LOG_DB'])
        log_db.log_verified(request.remote_addr)
        dark_term_db = DarkTermDB(app.config["DARK_TERM_DB"])
        header, body = backend.get_verified(dark_term_db)
        return render_template("body.html", header=header, body=body)

    @app.route('/content/usage/<term>', methods=['GET'])
    def usage(term):
        log_db = LogDB(app.config['LOG_DB'])
        log_db.log_dark_term_verified_click(term, request.remote_addr)
        timestamp_term = backend.get_usage_data(term, timestamp_data)
        kl_term = {
            forum_name: kl_data[forum_name][term][:num_clean_terms]
                   for forum_name in kl_data if term in kl_data[forum_name]
        }
        bert_term = {
            forum_name: bert_data[forum_name][term][:num_clean_terms]
                    for forum_name in bert_data if term in bert_data[forum_name]
        }
        return render_template(
            "usage.html", term=term, timestamp_term=timestamp_term, kl_term=kl_term, bert_term=bert_term
        )

    @app.route('/content/collab', methods=['POST', 'GET'])
    def collab():
        log_db = LogDB(app.config['LOG_DB'])
        if request.method == 'GET':
            log_db.log_collab_get(request.remote_addr)
            dark_term_db = DarkTermDB(app.config["DARK_TERM_DB"])
            header, body = backend.get_collab(dark_term_db)
            return render_template("collab.html", header=header, body=body)
        else:
            dark_term = request.form['dark_term']
            log_db.log_dark_term_collab_click(dark_term, request.remote_addr)
            definition = request.form['definition']
            definition_source = request.form['definition_source']
            user_name = request.form['user_name']
            dark_term_db = DarkTermDB(app.config["DARK_TERM_DB"])
            dark_term_db.insert_collab(dark_term, definition, definition_source, user_name)
            return 'success'

    @app.route('/content/thumbs_up/<dark_term_id>', methods=['POST'])
    def dark_term_thumbs_up(dark_term_id):
        log_db = LogDB(app.config['LOG_DB'])
        log_db.log_thumbs_up(dark_term_id, request.remote_addr)
        dark_term_db = DarkTermDB(app.config["DARK_TERM_DB"])
        dark_term_db.thumbs_up(dark_term_id)
        return 'success'

    @app.route('/content/thumbs_down/<dark_term_id>', methods=['POST'])
    def dark_term_thumbs_down(dark_term_id):
        log_db = LogDB(app.config['LOG_DB'])
        log_db.log_thumbs_down(dark_term_id, request.remote_addr)
        dark_term_db = DarkTermDB(app.config["DARK_TERM_DB"])
        dark_term_db.thumbs_down(dark_term_id)
        return 'success'

    @app.route('/content/download', methods=['GET'])
    def download():
        log_db = LogDB(app.config['LOG_DB'])
        log_db.log_download(request.remote_addr)
        return render_template("download.html")

    @app.route('/content/download_file/<dataset>', methods=['GET'])
    def download_file(dataset):
        log_db = LogDB(app.config['LOG_DB'])
        log_db.log_download_file(dataset, request.remote_addr)

        if dataset in ['verified', 'collab']:
            dark_term_db = DarkTermDB(app.config["DARK_TERM_DB"])
            file_ptr = download_handler.get_file_path(dataset, dark_term_db)
            file_ptr = file_ptr.replace('webapp/', '', 1)
            return send_file(file_ptr, as_attachment=True, attachment_filename=f'darkjargon-net_{dataset}.csv')
        if dataset == 'timestamps':
            return send_file('static/data/dark-terms_timestamps.pkl.gz',
                             as_attachment=True,
                             attachment_filename='dark-terms_timestamps.pkl.gz')
        if dataset == 'kl':
            return send_file('static/data/kl_clean-term-mapping.tar.gz',
                             as_attachment=True,
                             attachment_filename='kl_clean-term-mapping.tar.gz')
        if dataset == 'mlm-bert':
            return send_file('static/data/mlm-bert_clean-term-mapping.pkl.gz',
                             as_attachment=True,
                             attachment_filename='mlm-bert_clean-term-mapping.pkl.gz')
        # print error
        return 'Download Error'

    @app.route('/content/about', methods=['GET'])
    def about():
        log_db = LogDB(app.config['LOG_DB'])
        log_db.log_about(request.remote_addr)
        return render_template("about.html")

    return app
