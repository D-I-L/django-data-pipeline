''' Add search engine suggester to genes or markers index based on criteria. '''
import os
import sys
import json
import django

PYDGIN = None
if 'PYDGIN' in os.environ:
    PYDGIN = os.environ['PYDGIN']
else:
    print("ENV variable PYDGIN must be set to run this script")
    sys.exit()

sys.path.append(PYDGIN)
os.environ['DJANGO_SETTINGS_MODULE'] = 'pydgin.settings'
django.setup()

from elastic.management.loaders.loader import Loader
from elastic.elastic_settings import ElasticSettings
from elastic.search import ScanAndScroll, ElasticQuery, Search
from elastic.query import Query, TermsFilter

idx_criteria = 'imb_criteria'

gene_index = ''
if len(sys.argv) > 1:
    gene_index = sys.argv[1]

if gene_index != '':
    criteria_idx = 'pydgin_imb_criteria_gene'
    idx_type = 'gene'
    idx = 'genes_hg38_v0.0.2'
    feature_id = 'dbxrefs.ensembl'
    wt = 50
else:
    criteria_idx = 'pydgin_imb_criteria_marker'
    idx_type = 'marker'
    idx = 'dbsnp146'
    feature_id = 'id'
    wt = 0

update_count = 0
features = {}


def process_hits(resp_json):
    global features, update_count
    hits = resp_json['hits']['hits']

    for hit in hits:
        src = hit['_source']
        qid = src['qid']
        if qid in features:
            features[qid] = features[qid]+src['score']
        else:
            features[qid] = src['score']
    update_count += len(hits)
    print(str(update_count)+" of "+str(resp_json['hits']['total']))

scan_n_sroll = ScanAndScroll.scan_and_scroll(criteria_idx, call_fun=process_hits)

# Update suggest weights
update_count = 0
chunk_size = 2000
feature_names = list(features.keys())

for i in range(0, len(feature_names), chunk_size):
    feature_names_slice = feature_names[i:i+chunk_size]
    terms_filter = TermsFilter.get_terms_filter(feature_id, feature_names_slice)
    query = ElasticQuery.filtered(Query.match_all(), terms_filter, sources=[feature_id, 'suggest'])
    docs = Search(query, idx=idx, idx_type=idx_type, size=chunk_size).search().docs

    json_data = ''
    for doc in docs:
        doc_id = doc.doc_id()
        if feature_id.startswith('dbxrefs'):
            obj_id = getattr(doc, 'dbxrefs')['ensembl']
        else:
            obj_id = getattr(doc, feature_id)
        doc_data = {"update": {"_id": doc_id, "_type": idx_type,
                               "_index": idx, "_retry_on_conflict": 3}}
        json_data += json.dumps(doc_data) + '\n'

        suggest = getattr(doc, 'suggest')
        if suggest is None:
            suggest = {}
            suggest["input"] = obj_id

        weight = int(features[obj_id])+wt
        suggest["weight"] = weight
        json_data += json.dumps({'doc': {'suggest': suggest, 'tags': {'weight': weight}}}) + '\n'
        update_count += 1

#         if obj_id == 'ENSG00000134242':
#             print(json_data)
#             sys.exit()
    if json_data != '':
        Loader().bulk_load(idx, idx_type, json_data)
    print("Update count = "+str(update_count))
