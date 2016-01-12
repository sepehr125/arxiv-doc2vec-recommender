from collections import namedtuple
import psycopg2
from flask import Flask
from flask import render_template
from flask import request
from gensim.models import Doc2Vec
from gensim.similarities.docsim import Similarity
import re

app = Flask(__name__)


"""Helpers"""
def get_subjects():
    query = "SELECT DISTINCT subject FROM articles;"
    # query = "SELECT COUNT(*) FROM (SELECT DISTINCT subject FROM articles) AS temp;"
    cur.execute(query)
    subjects = sorted([s[0] for s in cur.fetchall()])
    return subjects


@app.route('/')
def home():
    subjects = get_subjects()
    return render_template("main.html", subjects=subjects)

if __name__ == '__main__':
    
    # load model:
    model = Doc2Vec.load('models/doc2vec_2k_primary_key')

    # help read articles:
    fields = ["idx", "title", "authors", "subject", "abstract", "pubdate", "arxid"]
    Article = namedtuple("Article", fields)

    # run app in db connection context
    with psycopg2.connect(dbname='arxiv') as conn:
        with conn.cursor() as cur:
            app.run(debug=True)