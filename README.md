# SciExplorer

A document similarity engine for discovering related scientifc articles using distributed representation (Doc2Vec), trained on 600,000+ articles from Arxiv.org on AWS.

## Motivation
Knowledge required to tackle complex problems is often siloed in disciplines, each with their own unique lexica and citation communities. There's a tremendous opportunity in finding overlaps across disciplines that could lead to innovative research directions and more complex ideas. 

Recent advances in Natural Language Processing have given us new tools for overcoming the barrier to discovery. Specifically, a set of machine learning algorithms developed at Google (Word2Vec) learn to represent text using fixed number of dimensions, each of which encodes some aspect of that word's or document's meaning.

Here are some examples from pre-trained word vectors:
Iraq - Violence = Jordan
Human - Animal = Ethics
President - Power = Prime Minister
Library - Books = Hall

Additionally, the cosine similarity between texts tends to reveal semantic similarity ("strong" and "powerful" will likely have a cosine similarity of approximately 1).


## How SciExplorer works
SciExporer's engine utilizes Word2Vec and Doc2Vec, which produce word and document vectors via a simple, 2-level neural network that trains on raw text, analyzing words in their local context. 
