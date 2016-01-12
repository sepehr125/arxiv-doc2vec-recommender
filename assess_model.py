from collections import namedtuple
import psycopg2
from gensim.models.doc2vec import Doc2Vec
import argparse

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="tests model's ability to predict tags of unseen documents")
    parser.add_argument('dbname', help="Name of postgres database")
    parser.add_argument('path_to_model', help="Filename to save the model to")
    args = parser.parse_args()

    model = Doc2Vec.load(path_to_model)
    docvecs_array = model.docvecs

    with psycopg2.connect(dbname='arxiv') as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM articles")        
            col_names = [col.name for col in cur.description]
            Article = namedtuple("Article", col_names)
            hits = 0
            for row in cur:
                article = Article(*row)
                relateds = model.docvecs.most_similar(positive=[article.index], topn=2)
                related_ids = tuple([idx for idx, similarity in relateds])
                with conn.cursor() as newcur:
                    newcur.execute("SELECT subject FROM articles WHERE index in %s"%(related_ids, ))
                    cats = newcur.fetchall()
                    new_hits = [1 if cat==article.subject else 0 for cat in cats]
                    hits += sum(new_hits)

    print(hits)