''' Data integrity tests for studies index '''

import logging

from django.conf import settings
from django.test import TestCase

from gene.document import GeneDocument
from region.document import RegionDocument
from study.document import StudyDocument


logger = logging.getLogger(__name__)


class StudyTest(TestCase):

    def test_genes_locations(self):
        ''' Test the chromosome matches the region for the gene(s) of interest. '''
        studies = StudyDocument.get_studies()
        err = ""
        gene_err = ""
        for study in studies:
            hits = RegionDocument.get_hits_by_study_id(study.doc_id(), sources=['chr_band', 'genes', 'marker',
                                                                                'alleles', 'pmid', 'build_info',
                                                                                'disease_locus'])
            for hit in hits:
                genes = getattr(hit, 'genes')
                chr_band = getattr(hit, 'chr_band')
                build_info = getattr(hit, 'build_info')
                for bi in build_info:
                    if bi['build'] == settings.DEFAULT_BUILD:
                        hit_loc = bi

                chromo = hit_loc['seqid']
                hit_start = hit_loc['start']
                hit_stop = hit_loc['end']
                if genes:
                    for ens_id in genes:
                        gene = GeneDocument.get_genes(ens_id, sources=['chromosome', 'symbol', 'start', 'stop'])
                        if len(gene) == 1:
                            gene_start = getattr(gene[0], 'start')
                            gene_stop = getattr(gene[0], 'stop')
                            msg = (study.doc_id()+" "+chr_band+" chr:" +
                                   chromo+":"+str(hit_start)+"-"+str(hit_stop) + " \t" +
                                   getattr(gene[0], 'symbol') + " chr" + getattr(gene[0], 'chromosome') + ":" +
                                   str(gene_start)+"-"+str(gene_stop)+"\n")
                            if getattr(gene[0], 'chromosome') != chromo:
                                if getattr(gene[0], 'symbol') != 'MIR548AN':  # mis-aligned gene in study GDXHsS00030
                                    err += msg
                            elif gene_stop < hit_start - 500000:
                                gene_err += msg
                            elif gene_start > hit_stop + 500000:
                                gene_err += msg

        if gene_err != "":
            print("\nRegion / Gene Position Mismatch")
            print(gene_err)

        if err != "":
            print("\nRegion / Gene Chromosome Mismatch")
            print(err)
            self.assertTrue(False, "gene(s) of interest match region location")
