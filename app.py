from collections import namedtuple, defaultdict, OrderedDict
import psycopg2
from flask import Flask
from flask import render_template
from flask import request
from gensim.models import Doc2Vec
from gensim.similarities.docsim import Similarity
import re
import argparse

app = Flask(__name__)


"""Helpers"""
def get_subjects():
    query = "SELECT DISTINCT subject FROM articles;"
    # query = "SELECT COUNT(*) FROM (SELECT DISTINCT subject FROM articles) AS temp;"
    cur.execute(query)
    subjects = sorted([s[0] for s in cur.fetchall()])
    return subjects
    # d = defaultdict(list)
    # for s in subjects:
    #     parent_child = s.split(' - ')
    #     if len(parent_child) == 2:
    #         d[parent_child[0]].append(parent_child[1])
    #     elif len(parent_child) == 1:
    #         d[parent_child[0]] = []

    # return OrderedDict(sorted(d.items()))


@app.route('/subjects')
def browse_subjects():
    return render_template("browse.html", subjects=get_subjects())

@app.route('/')
def home():
    
    # like = request.args.get('like', '')
    # unlike = request.args.get('unlike', '')
    # return like.split(',')
    return render_template("main.html", subjects=get_subjects())

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Fire up flask server with appropriate model')
    parser.add_argument('model_path', help="Name of model file")
    args = parser.parse_args()

    # load model:
    model = Doc2Vec.load(args.model_path)

    # help read articles:
    fields = ["idx", "title", "authors", "subject", "abstract", "pubdate", "arxid"]
    Article = namedtuple("Article", fields)

    # run app in db connection context
    with psycopg2.connect(dbname='arxiv') as conn:
        with conn.cursor() as cur:
            app.run(debug=True)