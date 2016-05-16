''' GWAS/IC statistics index data. '''
import logging
import re

from elastic.management.loaders.loader import Loader, JSONLoader
from elastic.management.loaders.mapping import MappingProperties


logger = logging.getLogger(__name__)


class AssocStats(object):
    ''' GWAS/IC stats data
    chr    position    dbSNP    p-value    OR    OR_lower    OR_upper    raf risk_allele    alt_allele    imputed
    1       113834946       rs2476601       3.83077315885e-17       1.2034  1.1602  1.2465  0.902   G       A       0
    '''

    @classmethod
    def mapping(cls, idx, idx_type, meta):
        ''' Create the mapping for gwas/ic stats indexing '''
        props = MappingProperties(idx_type)
        props.add_property("seqid", "string")
        props.add_property("position", "integer")
        props.add_property("marker", "string", index="not_analyzed")
        props.add_property("p_value", "double")
        props.add_property("odds_ratio", "float")
        props.add_property("lower_or", "float", index="no")
        props.add_property("upper_or", "float", index="no")
        props.add_property("raf", "float", index="no")
        props.add_property("risk_allele", "string", index="no")
        props.add_property("alt_allele", "string", index="no")
        props.add_property("imputed", "byte", index="no")

        load = Loader()
        options = {"indexName": idx, "shards": 5}
        load.mapping(props, idx_type, meta=meta, **options)

    @classmethod
    def idx(cls, f, idx, idx_type):
        ''' Parse and load data for association stats. '''

        new_docs = []
        chunk_size = 500
        count = 0

        for line in f:
            line = line.strip()
            if line.startswith("#"):
                continue
            parts = re.split('\t', line)
            data = {
                "seqid": parts[0],
                "position": int(parts[1]),
                "marker": parts[2],
                "p_value": float(parts[3]),
                "risk_allele": parts[8],
                "alt_allele": parts[9]
            }

            if isfloat(parts[4]) and float(parts[4]) > 0:
                data['odds_ratio'] = float(parts[4])
            if isfloat(parts[5]) and float(parts[5]) > 0:
                data['or_lower'] = float(parts[5])
            if isfloat(parts[6]) and float(parts[6]) > 0:
                data['or_upper'] = float(parts[6])
            if isfloat(parts[7]) and float(parts[7]) > 0:
                data['raf'] = float(parts[7])
            if isint(parts[10]) and int(parts[10]) >= 0:
                data['imputed'] = int(parts[10])

            new_docs.append(data)

            if count > chunk_size:
                JSONLoader().load(new_docs, idx, idx_type)
                new_docs = []
                count = 0
            count += 1

        if len(new_docs) > 0:
            JSONLoader().load(new_docs, idx, idx_type)


def isfloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


def isint(value):
    try:
        int(value)
        return True
    except ValueError:
        return False
