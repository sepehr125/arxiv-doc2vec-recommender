import pickle
import pandas as pd
import gensim
from gensim.models.doc2vec import Doc2Vec
import psycopg2
import psycopg2.extras
import numpy as np
from scipy.spatial.distance import pdist, squareform
import argparse

"""
Note: You have to have ran cache_subject_hash.py before
running this script.

This produces a CSV file that d3 looks for
to create a visualization of topics and their
distances. 

We first calculate the average vector of articles per subject,
Then calculate the pairwise distance of these topic vectors,
and lastly produce a CSV that relates the n closest topics,
with one relationship per row.
"""

def get_subject_hash(dbname):
    """
    INPUT: (str) name of database containing the subjects table.
    NOTE: The subject table is produces by cache_subject_hash.py
    which must be run first
    OUTPUT: (dict) {subject_id: subject_name}
    """
    with psycopg2.connect(dbname=dbname) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT index, subject FROM subjects;")
            results = cur.fetchall()
            subject_hash = {i[0]: i[1] for i in results}
            return subject_hash

def get_subject_vectors(subject_ids):
    """
    Get panda DataFrame where each row is a subject's average docvec
    and index is the subject_id
    """
    subject_vectors = {}
    with psycopg2.connect(dbname='arxiv') as conn:
        for subject_id in subject_ids:
            cur = conn.cursor()
            cur.execute("SELECT index FROM articles WHERE subject_id='%s'"%subject_id)
            article_ids = cur.fetchall()
            article_vectors = np.array([model.docvecs[id[0]] for id in article_ids])
            subject_vectors[subject_id] = np.mean(article_vectors, axis=0)
    # turn the dictionary into a dataframe and return
    return pd.DataFrame(subject_vectors).T

def get_distance_mat(subject_vectors, dist='cosine'):
    """
    returns pandas dataframe where indices and col_names
    are subject_ids, and each cell (i,j) is the distance between
    the subjects (i,j)
    """
    # dense matrix of distance pairs between subject vectors
    Y = squareform(pdist(subject_vectors, dist))
    # transfer subject_ids as index to Y:
    distance_mat = pd.DataFrame(Y, index=subject_vectors.index, columns=subject_vectors.index)
    return distance_mat

def get_n_closest(distance_mat, subject_id, n=5):
    """
    Sorts a distance matrix's column for a particular subject and returns 
    n closest subject_ids
    """
    s = distance_mat.loc[subject_id]
    closest = s.sort_values()[1:1+n]
    return closest


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="produce similarity matrix")
    parser.add_argument('dbname', help="Database name")
    parser.add_argument('path_to_model', help="Model to test")
    parser.add_argument('n_closest', help="How many closest subjects to look into")
    args = parser.parse_args()

    model = Doc2Vec.load(args.path_to_model)

    subject_hash = get_subject_hash(args.dbname)
    subject_ids = list(subject_hash.keys())

    # loop over subjects and average docvecs belonging to subject.
    # place in dictionary
    subject_vectors = get_subject_vectors(subject_ids)
    distance_mat = get_distance_mat(subject_vectors)

    to_csv = []
    for subj_id in subject_ids:
        relateds = get_n_closest(distance_mat, subj_id, n=int(args.n_closest))
        for related_id, dist in relateds.iteritems():
            weight = round(1./dist)
            #weight = round((1-dist) * 10)
            row = (subj_id, related_id, weight, subject_hash[subj_id], subject_hash[related_id])
            to_csv.append(row)

    edges = pd.DataFrame(to_csv, columns=['source', 'target', 'weight', 'source_name', 'target_name'])
    edges.to_csv('../static/subject_distances.csv', index=False)
