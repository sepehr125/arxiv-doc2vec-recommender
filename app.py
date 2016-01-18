# -*- coding: utf-8 -*-
from operator import itemgetter
import psycopg2
from psycopg2.extras import DictCursor
from flask import Flask, render_template, request, url_for
from gensim.models import Doc2Vec
import re
import argparse

application = Flask(__name__)

"""Helpers"""

def get_subjects():
    """
    OUTPUT: list of tuples containing:
            (subject name, count)
            where count is the number of articles in subject,
            ordered alphabetically by subject name
    
    Called by browse_subjects()
    """
    cur = conn.cursor()
    cur.execute("SELECT subject, COUNT(*) FROM articles GROUP BY subject;")
    subjects = sorted(cur.fetchall(), key=lambda tup:tup[0])
    return subjects


def get_articles(indices):
    """
    INPUT: list of integers corresponding to
        'index' column values of desired articles in database

    OUTPUT: list of dictionaries, each dictionary
        corresponding to an article
    """
    with conn.cursor(cursor_factory=DictCursor) as cur:
        query = "SELECT * FROM articles \
            WHERE index IN %s \
            ORDER BY last_submitted DESC"
        cur.execute(query, (tuple(indices),))
        articles = cur.fetchall()
        return articles


def get_articles_by_subject(subject):
    """
    INPUT: 
        (str): subject name

    OUTPUT: list of dictionaries, each dictionary
        corresponding to an article
    """
    with conn.cursor(cursor_factory=DictCursor) as cur:
        query = "SELECT * FROM articles \
            WHERE subject=%s \
            ORDER BY last_submitted DESC"
        cur.execute(query, (subject,))
        articles = cur.fetchall()
        return articles


def get_article(index):
    """
    INPUT: 
        (int): article index

    OUTPUT: 
        (dict): dictionary object representing 
            article matching the given index
    """
    with conn.cursor(cursor_factory=DictCursor) as cur:
        query = "SELECT * FROM articles WHERE index=%s"
        cur.execute(query, (index, ))
        article = cur.fetchone()
        return article

"""
ROUTES
"""

@application.route('/')
@application.route('/topics/')
@application.route('/topics/<subject>')
def browse_subjects(subject=None):
    """
    Route for displaying home page, 
    list of subjects (currently the same thing)
    or the list of articles by given subject
    """
    if subject is None:
        return render_template("browse.html", subjects=get_subjects())
    else:
        articles = get_articles_by_subject(subject)
        return render_template("articles.html", articles=articles, subject=subject)

@application.route('/article/<main_article_id>')
def find_similars(main_article_id=None):
    main_article = get_article(main_article_id)
    sims = model.docvecs.most_similar(int(main_article_id), topn=10) # list of (id, similarity)
    sim_articles = get_articles([int(index) for index, sim in sims]) # list of dictionaries...
    # we're gonna add similarity scores to each dictionary (article) in above list from sims
    sort_these = []
    for article in sim_articles:
        sim_score = [score for idx, score in sims if article['index'] == idx ][0]
        article.extend([round(sim_score, 2)])
        sort_these.append(article)

    return render_template("doc.html", main_article=main_article, sims=sort_these)

@application.route('/search', methods=['POST'])
def search():
    if request.method == 'POST':
        query = request.form['search']
        q_vec = model.infer_vector(query.split())
        results = model.docvecs.most_similar(positive=[q_vec], topn=100)
        results = [int(r[0]) for r in results]
        results = get_articles(results)
        return render_template("search.html", articles=results, q=query)

@application.route('/analogy')
def find_analogy():
    """
    king - man + woman = queen
    aka:
    king:man :: queen:woman

    Here we expose a way to query our model
    to find analogies.
    As of right now, the analogies are not ready for prime time,
    but the URL is up as an easter egg.
    """
    like1 = request.args.get('like1', '') # king
    like2 = request.args.get('like2', '') # + woman
    unlike = request.args.get('unlike', '') # - man

    likes = [word.lower() for word in [like1, like2] if word != '']
    unlike = [word.lower() for word in list(unlike) if word not in ('', '#')]

    if not likes and not unlike:
        return render_template("analogy.html", analogies=[], error=False)
    try:
        analogies = model.most_similar(positive=likes, negative=unlike)
        return render_template("analogy.html", analogies=analogies)
    except:
        return render_template("analogy.html", analogies=[], error=True)


@application.route('/viz')
def viz():
    """
    If we think of similarity as a weight 
    connecting articles and topics,
    we have a weighted graph.
    For topic modeling, a community detection
    algorithm could be used on this weighted 
    graph to identify and visualize clusters.
    This is what the louvain template does for
    topics.

    I hope to expand this visualization to 
    articles in each topic.
    """
    csv_dest = url_for('static', filename='subject_distances.csv')
    return render_template("louvain.html", csv_dest=csv_dest)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Fire up flask server with appropriate model')
    parser.add_argument('model_path', help="Name of model file")
    parser.add_argument('port', help="Port to run on", default=5000)
    args = parser.parse_args()

    # run app in db connection context
    with psycopg2.connect(dbname='arxiv') as conn:
        # load model:
        model = Doc2Vec.load(args.model_path)
        application.run(host='0.0.0.0', port=int(args.port), debug=True)
