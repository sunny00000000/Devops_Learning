"""
Billinger v3.0 Features Layer: Master Curriculum, 3-Tier Command Guard & Document Classifier
Directly integrates with security.guard, learning.catalog, and documents.classifier.
"""
from security.guard import command_guard, CommandGuard
from learning.catalog import catalog, DevOpsCatalog as Catalog
from documents.classifier import document_classifier, DocumentClassifier
from documents.ingestion import document_ingestion, DocumentIngestion

class MasterCurriculumEngine:
    def __init__(self):
        self.catalog = catalog

    def get_domains(self):
        return self.catalog.domains

    def get_domain_by_id(self, domain_id):
        return self.catalog.get_domain(domain_id)

curriculum_engine = MasterCurriculumEngine()
