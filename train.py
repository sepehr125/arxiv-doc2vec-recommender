import multiprocessing
import psycopg2
from psycopg2.extras import DictCursor
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
import re
import argparse


class DocIterator(object):
    """
    gensim documentation calls this "streaming a corpus", which 
    lets us train without holding entire corpus in memory.
    Doc2Vec requires two passes over the data, so it is necessary
    to create this iterator object that it can call twice.
    Here, we stream from a postgres database.
    """

    def __init__(self, conn):
        self.conn = conn

    def __iter__(self):
        with conn.cursor(cursor_factory=DictCursor) as cur:
            # I'd really like to store names of databases, tables, columns
            # in a central location, possibly a json file or pickled dict
            # that various files can use.
            cur.execute("SELECT * FROM articles;")
            for index, title, authors, subject, abstract, pubdate, arxiv_id, subject_id in cur:
                body = title + '. ' + abstract
                words = re.findall(r"[\w']+|[.,!?;]", body)
                words = [word.lower() for word in words]
                tags = [index]
                yield TaggedDocument(words, tags)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='trains model based on corpus in psql')
    parser.add_argument('dbname', help="Name of postgres database")
    parser.add_argument('path_to_model', help="Filepath and name for model")
    args = parser.parse_args()

    n_cpus = multiprocessing.cpu_count()
    with psycopg2.connect(dbname=args.dbname) as conn:
        doc_iterator = DocIterator(conn)
        model = Doc2Vec(documents=doc_iterator, workers=n_cpus)

    model.save(args.path_to_model)
    print("Model can be found at %s"%args.path_to_model)
    
