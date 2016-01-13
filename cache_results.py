import psycopg2
from gensim.models.doc2vec import Doc2Vec
import argparse

def create_schema(db, table):
    conn = psycopg2.connect(dbname=db)
    cur = conn.cursor()
    sql_create = """
    DROP TABLE IF EXISTS %s;
    CREATE TABLE IF NOT EXISTS %s (
        article_A integer,
        article_B integer,
        similarity real
    );"""%(table, table)
    cur.execute(sql_create)
    conn.commit()
    conn.close()

def insert_relation(conn, table, article_A, relateds):
    with conn.cursor() as cur:
        for article_B, similarity in relateds:
            cur.execute("INSERT INTO %s VALUES (%s, %s, %s)"%(table, article_A, article_B, similarity))
        conn.commit()


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Takes a model's assessment of doc similarity and saves it to database")
    parser.add_argument('db', help="Name of postgres database")
    parser.add_argument('table', help="Name of postgres table")
    parser.add_argument('model_path', help="Path to model that we will cache")
    parser.add_argument('n_similars', help="Number of similar items to cache")
    # parser.add_argument('threshold', help="Similarity threshold for ")
    args = parser.parse_args()

    model = Doc2Vec.load(args.model_path)
    with psycopg2.connect(dbname=args.db) as conn:
        create_schema(args.db, args.table)
        with conn.cursor() as cur:
            cur.execute("SELECT index FROM articles")
            for article_A in cur:
                index_A = article_A[0]
                relateds = model.docvecs.most_similar(positive=[index_A], topn=int(args.n_similars))
                insert_relation(conn, args.table, index_A, relateds)