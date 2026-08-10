# Bolt's Journal

## 2025-02-17 - Broad Try/Except Antipattern
**Learning:** Broad try/except blocks in app.py can swallow HTTPExceptions (such as 'Empty file' or 'File too large') preventing accurate error reporting. Catching HTTPException explicitly avoids this anti-pattern.
**Action:** Always handle HTTPException first and re-raise it when implementing custom error boundaries in FastAPI.
