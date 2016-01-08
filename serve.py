from flask import Flask
from flask import render_template
from flask import request
from gensim.models import Doc2Vec
from gensim.similarities.docsim import Similarity
from pymongo.mongo_client import MongoClient
import re

app = Flask(__name__)


"""
HELPERS
"""
def get_similars(key, num_similars=10):
    docvecs_array = model.docvecs
    original_vector = docvecs_array[key]
    similars = docvecs_array.most_similar(positive=[original_vector], topn=num_similars)[1:]
    output = []
    for sim_id, sim_degree in similars:
        output.append(collection.find_one({'id': sim_id}))
    return output


def search_regex(query):
    words = query.split()
    return re.compile('|'.join(words), re.IGNORECASE)

@app.context_processor
def utility_processor():
    def get_slug(arxiv_url):
        return arxiv_url.split('/').pop()
    return dict(get_slug=get_slug)

"""
ROUTES
"""
@app.route("/")
def home():
    article = collection.find_one()
    similars = get_similars(article['id'])
    return render_template("main.html", article=article, similars=similars)

@app.route("/like/<criteria>/<path:key>")
def like(criteria, key):
    if criteria == 'id':
        arxiv_id = 'http://arxiv.org/abs/' + key
        article = collection.find({'id': arxiv_id}).next()
        similars = get_similars(arxiv_id)
    elif criteria == 'author':
        author = collection.find({'author': key}).next()
        similars = get_similars(author)
    else:
        return "bad criteria"

    return render_template("main.html", article=article, similars=similars)


@app.route("/cat/<cat_id>")
def docs_by_cat(cat_id):
    docs = collection.find({'arxiv_primary_category': {'term': cat_id}})


@app.route("/viz")
def viz():
    cat = request.args.get('cat', '')
    docs = collection.find({'arxiv_primary_category.term': cat})
    csv = ''
    data = []
    for doc in docs:
        for similar, weight in doc['similars']:
            # csv += "'%s', '%s', '%s'\n"%(doc['id'], similar, str(round(weight, 3)) + '\n'
            data.append((doc['id'], similar, round(weight, 3)))

    return render_template("viz.html", data=data)

@app.route("/search/<q>")
def search(q):
    # infer vector for q, return similars:
    q_vec = model.infer_vector(q)
    similars = model.most_similar(positive=[q_vec])
    return str(similars)

    # regx = search_regex(q)
    # matches = collection.find({"title": regx}, limit=10)
    # match_list = [match for match in matches]
    # return render_template("search.html", results=list(matches), query=q)
    

if __name__ == '__main__':
    
    # load model:
    model = Doc2Vec.load('models/doc2vec_22k_cat_in_abstract')

    # connect to db:
    client = MongoClient()
    collection = client.arxiv.articles

    app.run(debug=True)