from gensim.models import Doc2Vec
from pymongo.mongo_client import MongoClient

def 
model = Doc2Vec.load(path_to_model)
docvecs_array = model.docvecs

# connect to mongo
client = MongoClient()
collection = client.arxiv.articles

def get_cat(arxid, collection, parent_only=False):
    res = collection.find_one({'id': arxid}, ['arxiv_primary_category'])
    cat = res['arxiv_primary_category']['term']
    if parent_only:
        return cat.split(".")[0]
    else:
        return cat


hit = 0
parent_hit = 0
cats = []
for item in collection.find():
    item_vec = docvecs_array[item['id']]
    # relateds is list of (id, similarity) pairs, skip first b/c self-similarity == 1
    relateds = docvecs_array.most_similar(positive=[item_vec], topn=3)[1:]
    original_cat = get_cat(item['id'], collection)
    related_cats = [get_cat(i, collection) for i, sim in relateds]
    # if categories are the same
    if original_cat in related_cats:
        hit += 1
    # if parent cats are the same
    if original_cat.split('.')[0] in [cat.split('.')[0] for cat in related_cats]:
        parent_hit += 1
    # to get a distribution of categories in the corpus:
    cats.append(original_cat)

print("Percent of top recommendations in same category:")
print(hit / len(cats) * 100)

print("Percent of top recommendations in same parent category:")
print(parent_hit / len(cats) * 100)
