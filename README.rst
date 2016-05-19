=============
data_pipeline
=============

The data pipeline is configured using ini files. Note that the ELASTIC settings are taken
from the pydgin module (i.e. pydgin/settings_secret.py).

Publication Pipeline
--------------------

The publication.ini is used to define the configuration for downloading,
staging/processing and loading/indexing. To run the publication pipeline::

    ./manage.py publications --dir tmp --ini publications.ini \
                             --steps download stage load

Or step-by-step::

    ./manage.py publications --dir tmp --ini publications.ini \
                             --sections GENE --steps download stage
    ./manage.py publications --dir tmp --ini publications.ini \
                             --sections GENE --steps load

    ./manage.py publications --dir tmp --ini publications.ini \
                             --sections [DISEASE::T1D],[DISEASE::CRO] \
                             --steps  download load

The publication pipeline is incremental so that when run multiple times it
will query EUTILS only for new publications it finds and add those to the index.

Note a useful terms aggregation for finding the number of documents per disease::

    curl 'http://127.0.0.1:9200/publications/_search?size=1&from=0&pretty' \
       -d '{"aggs": {"disease_groups": {"terms": {"field": "disease", "size": 0}}}}'

    curl 'http://127.0.0.1:9200/publications/_search?size=0&from=0&pretty' \
       -d '{"aggs": {"missing_disease_groups": {"missing": {"field": "disease"}}}}'


Data Pipeline
-------------

Details for running each part of the data pipeline (e.g. gene, marker)
can be found in the API documentation in data_pipeline/management/commands/pipeline.py.

Tests
-----

./manage.py test data_pipeline.tests

Data Integrity Tests
--------------------

./manage.py test data_pipeline.data_integrity

