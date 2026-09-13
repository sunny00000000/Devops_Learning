from storage.db import db

class DocumentSearch:
    @staticmethod
    def search(query: str, tool_filter: str = None) -> list:
        q = f"%{query.strip()}%"
        if tool_filter:
            sql = "SELECT id, filename, domain, primary_tool, confidence, version, content_text FROM documents WHERE primary_tool = ? AND (filename LIKE ? OR content_text LIKE ?) LIMIT 20"
            rows = db.fetchall(sql, (tool_filter, q, q))
        else:
            sql = "SELECT id, filename, domain, primary_tool, confidence, version, content_text FROM documents WHERE filename LIKE ? OR content_text LIKE ? LIMIT 20"
            rows = db.fetchall(sql, (q, q))

        results = []
        for r in rows:
            text = r.get("content_text") or ""
            idx = text.lower().find(query.lower())
            snippet = text[max(0, idx - 80):min(len(text), idx + 160)] if idx != -1 else text[:150]
            results.append({
                "id": r["id"],
                "filename": r["filename"],
                "domain": r["domain"],
                "primary_tool": r["primary_tool"],
                "confidence": r["confidence"],
                "version": r["version"],
                "snippet": snippet.strip()
            })
        return results

document_search = DocumentSearch()
