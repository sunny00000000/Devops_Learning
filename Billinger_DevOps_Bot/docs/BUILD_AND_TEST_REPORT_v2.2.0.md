# Billinger Bot v2.2.0 Build and Classification Report

- 69 PDF/DOCX resource pairs indexed: 65 technical course books + 4 program-wide guides.
- 2,976 indexed PDF pages and approximately 905,897 words.
- All 65 technical books have exactly one verified primary tool.
- 139 old cross-tool display placements were removed.
- Program-wide guides are isolated in Program Library.
- Dashboard redesigned with grouped, independently scrollable navigation and a dedicated Program Library reader.
- Local-only architecture, SQLite progress, Safe Real Lab restrictions and existing learning/test/interview features are retained.

## Validation completed

- Python compilation: passed
- JavaScript syntax validation: passed
- Automated unit tests: 22 passed
- Core HTTP smoke test: passed
- v2 company/lab/recruitment HTTP smoke test: passed
- 69 PDF hashes matched their source ZIP entries
- 69 DOCX hashes matched their source ZIP entries
- Strict-classification checks for Linux, Git, Ansible and CI/CD: passed
- Program Library resource listing, reading and source-grounded Q&A: covered by API and unit tests

## Important placement rule

The 65 technical books are never duplicated across tool lists. Related-topic metadata remains searchable, but placement is controlled only by `primary_tool`. The four program-wide resources use `placement=program` and do not appear in any technical tool list.
