# Data Directory

This directory contains all data used in the project, organized by processing stage.

## Structure

### raw/
Original, unmodified data from external sources.
- Should not be modified after ingestion
- Preserved for reproducibility
- Examples: original PDFs, lecture notes, raw text files

### interim/
Intermediate data that has been processed but not yet finalized.
- Data in various stages of transformation
- May be discarded after final processing
- Examples: extracted text, cleaned documents

### processed/
Final, processed datasets ready for use in models or analysis.
- Clean, validated data
- Ready for embedding generation
- Examples: chunked documents, metadata

### external/
Data from external sources or third-party datasets.
- Reference data
- Pre-trained embeddings (if used)
- External knowledge bases

## Guidelines
- Do not commit large binary files to Git
- Use `.gitignore` to exclude data files
- Document data sources and processing steps
- Maintain data versioning through naming conventions

## Data Privacy
- Ensure no personal or sensitive information is stored
- Comply with university data policies
- Anonymize user data if collected

---

**Status:** Empty - Awaiting data collection phase
