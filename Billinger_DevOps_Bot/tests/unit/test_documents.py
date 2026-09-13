"""
Unit tests for Document Ingestion, Strict Classification, and Versioning.
"""
import unittest
import sys
import tempfile
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from documents.classifier import document_classifier
from documents.ingestion import document_ingestion
from documents.search import document_search

class TestDocuments(unittest.TestCase):
    def test_strict_classification_no_mixing(self):
        linux_doc = "systemd journalctl fdisk -l /dev/sda1 sysctl -w net.ipv4.ip_forward=1"
        c1 = document_classifier.classify("linux_admin.txt", linux_doc)
        self.assertEqual(c1["primary_tool"], "Linux")
        self.assertEqual(c1["domain"], "Linux SysAdmin")

        k8s_doc = "kubectl get pods -A statefulset helm install ingress-nginx"
        c2 = document_classifier.classify("k8s_guide.md", k8s_doc)
        self.assertEqual(c2["primary_tool"], "Kubernetes")
        self.assertEqual(c2["domain"], "Container Orchestration")

        tf_doc = "terraform plan -out=tfplan opentofu hcl2 state lock s3 backend"
        c3 = document_classifier.classify("terraform_main.txt", tf_doc)
        self.assertEqual(c3["primary_tool"], "Terraform")

    def test_document_ingestion_and_search(self):
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
            f.write("# Ansible Automation\nansible-playbook -i inventory.ini site.yml with ansible-vault secrets\n")
            temp_path = f.name

        try:
            res = document_ingestion.ingest_file(temp_path, filename="ansible_guide.md")
            self.assertIn(res["status"], ["INGESTED", "DUPLICATE_DETECTED"])
            hits = document_search.search("ansible-playbook")
            self.assertGreater(len(hits), 0)
            self.assertEqual(hits[0]["primary_tool"], "Ansible")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
