import os
import hashlib
import time
from pathlib import Path
from storage.db import db
from core.errors.exceptions import ValidationError

class DocumentIngestion:
    @staticmethod
    def compute_sha256(filepath: Path) -> str:
        hasher = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    @classmethod
    def ingest_file(cls, filepath_str: str, filename: str = None) -> dict:
        filepath = Path(filepath_str)
        if not filepath.exists():
            raise ValidationError(f"File not found: {filepath_str}")

        fname = filename or filepath.name
        fhash = cls.compute_sha256(filepath)
        
        existing = db.fetchone("SELECT id, filename, version FROM documents WHERE file_hash = ?", (fhash,))
        if existing:
            return {
                "status": "DUPLICATE_DETECTED",
                "id": existing["id"],
                "filename": existing["filename"],
                "file_hash": fhash,
                "version": existing["version"],
                "message": "Exact byte-for-byte duplicate already indexed in library."
            }

        ext = filepath.suffix.lower()
        extracted_text = ""
        try:
            if ext in (".txt", ".md", ".csv", ".json"):
                with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                    extracted_text = f.read()
            elif ext == ".pdf":
                try:
                    import pypdf
                    reader = pypdf.PdfReader(str(filepath))
                    extracted_text = "\n".join(page.extract_text() or "" for page in reader.pages)
                except Exception:
                    extracted_text = f"[PDF Document {fname} - binary indexed]"
            elif ext == ".docx":
                try:
                    import docx
                    doc = docx.Document(str(filepath))
                    extracted_text = "\n".join(p.text for p in doc.paragraphs)
                except Exception:
                    extracted_text = f"[DOCX Document {fname} - binary indexed]"
            else:
                extracted_text = f"[{ext.upper()} Document {fname}]"
        except Exception as e:
            extracted_text = f"Extraction fallback for {fname}: {e}"

        from documents.classifier import document_classifier
        classification = document_classifier.classify(fname, extracted_text)

        doc_id = f"doc_{fhash[:12]}"
        db.execute("""
            INSERT INTO documents (id, filename, file_hash, domain, primary_tool, confidence, version, duplicate_status, content_text, ingested_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            doc_id, fname, fhash,
            classification["domain"], classification["primary_tool"],
            classification["confidence"], classification["version"],
            "ORIGINAL", extracted_text[:65536], time.time()
        ))

        return {
            "status": "INGESTED",
            "id": doc_id,
            "filename": fname,
            "file_hash": fhash,
            "classification": classification
        }

document_ingestion = DocumentIngestion()
