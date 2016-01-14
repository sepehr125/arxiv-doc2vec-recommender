from collections import namedtuple
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

def get_articles(indices):
    with conn.cursor() as cur:
        if type(indices) == list:
            query = cur.mogrify("SELECT * FROM articles WHERE index IN %s", (tuple(indices),))
            cur.execute(query)
            col_names = [col.name for col in cur.description]
            Article = namedtuple("Article", col_names)
            articles = [Article(*row) for row in cur.fetchall()]
            return articles

@app.route('/subjects')
def browse_subjects():
    return render_template("browse.html", subjects=get_subjects())

@app.route('/doc/<doc_id>')
def find_similars(doc_id):
    doc = get_articles(list(doc_id)).pop()
    sims = model.docvecs.most_similar(int(doc_id))
    sim_indices = [int(index) for index, similarity in sims]
    sim_articles = get_articles(sim_indices)
    return render_template("doc.html", doc=doc, sims=sim_articles)


@app.route('/')
def home():
    
    # like = request.args.get('like', '').split(',')
    # unlike = request.args.get('unlike', '').split(',')
    # in_subject = request.args.get('in', '').split(',')
    # not_in_subject = request.args.get('not_in', '').split(',')

    return render_template("main.html")

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
        app.run(debug=True, port=5000, host='0.0.0.0')
