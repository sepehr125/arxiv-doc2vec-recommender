import os
import feedparser
from pymongo.mongo_client import MongoClient

coll = MongoClient().arxiv.articles

errs = []
for fname in os.listdir('raw'):
    with open('raw/' + fname) as f:
        txt = f.read()
        parse = feedparser.parse(txt)
        if len(parse.entries) > 0: 
            result = coll.insert_many(parse.entries)
            print("Inserted %d records"%len(result.inserted_ids))
        else:
            errs.append(fname)

print("Unable to parse %d files"%len(errs))