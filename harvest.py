"""
Harvest metadata of ArXiv articles (including abstract)
for given subject or date range
from Open Archives Initiative (OAI).
More information: http://arxiv.org/help/oa/index

make sure you have installed oaiharvest already:
https://pypi.python.org/pypi/oaiharvest
"""


# run this at the terminal:
# oai-harvest -from 2016-01-01 -until 2016-01-07 http://export.arxiv.org/oai2

# by default, the metadataPrefix is set to "oai_dc"
# which specifies the XML format.