from storage.db import db
import difflib

class DocumentVersioning:
    @staticmethod
    def list_document_versions(filename: str) -> list:
        return db.fetchall("SELECT * FROM documents WHERE filename = ? ORDER BY ingested_at DESC", (filename,))

    @staticmethod
    def compare_versions(doc_id_1: str, doc_id_2: str) -> dict:
        d1 = db.fetchone("SELECT filename, version, content_text FROM documents WHERE id = ?", (doc_id_1,))
        d2 = db.fetchone("SELECT filename, version, content_text FROM documents WHERE id = ?", (doc_id_2,))
        
        if not d1 or not d2:
            return {"error": "One or both document IDs not found"}

        text1 = (d1.get("content_text") or "").splitlines()
        text2 = (d2.get("content_text") or "").splitlines()

        diff = list(difflib.unified_diff(text1, text2, fromfile=f"{d1['filename']} v{d1['version']}", tofile=f"{d2['filename']} v{d2['version']}"))
        return {
            "doc1": {"id": doc_id_1, "version": d1["version"]},
            "doc2": {"id": doc_id_2, "version": d2["version"]},
            "diff": diff[:200]
        }

document_versioning = DocumentVersioning()
