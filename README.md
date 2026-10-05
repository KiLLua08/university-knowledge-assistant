# AI-Powered University Knowledge Assistant

## Status
🟡 Project initialization

## Overview
An AI-powered knowledge assistant designed for university students to help them understand and navigate their academic resources including course notes, lecture PDFs, TD/TP documents, exercises, previous exams, and academic references.

## Problem
University students often have large amounts of academic material distributed across PDFs, lecture notes, exercises, exams and other documents. Finding relevant information and understanding relationships between these resources can be difficult and time-consuming.

## Objectives
The project aims to build an AI assistant capable of:
- Processing large collections of educational documents
- Helping students retrieve relevant academic information
- Providing context-aware explanations
- Supporting semantic search across academic materials
- Source attribution for all answers

## Planned Technologies
- **Python**: Core programming language
- **PyTorch**: Deep learning framework
- **Hugging Face Transformers**: NLP models and embeddings
- **Apache Spark / PySpark**: Distributed data processing
- **PostgreSQL**: Relational database
- **Vector database**: Semantic search (to be selected)
- **FastAPI**: API framework
- **Docker**: Containerization
- **Git/GitHub**: Version control
- **Jupyter**: Interactive development

*Note: Technology choices may evolve based on experimentation.*

## Project Architecture
See [docs/architecture.md](docs/architecture.md) for detailed architecture documentation.

## Repository Structure
```
university-knowledge-assistant/
├── README.md                 # This file
├── LICENSE                   # Project license
├── .gitignore               # Git ignore rules
├── .env.example             # Environment variables template
├── requirements.txt          # Python dependencies
├── pyproject.toml          # Python project configuration
│
├── docs/                    # Project documentation
│   ├── project_scope.md     # Project scope and objectives
│   ├── architecture.md      # System architecture
│   ├── development_log.md   # Development milestones
│   └── decisions.md         # Technical decisions log
│
├── data/                    # Data directories
│   ├── raw/                 # Original, unmodified data
│   ├── interim/            # Intermediate processed data
│   ├── processed/           # Final processed datasets
│   └── external/            # External data sources
│
├── notebooks/               # Jupyter notebooks for experimentation
│   └── README.md
│
├── src/                     # Source code
│   └── university_knowledge_assistant/
│       ├── __init__.py
│       ├── config/          # Configuration management
│       ├── data/            # Data loading and ingestion
│       ├── preprocessing/  # Data preprocessing utilities
│       ├── models/          # ML/DL models
│       ├── retrieval/       # Information retrieval components
│       ├── pipelines/       # End-to-end pipelines
│       └── utils/           # Utility functions
│
├── tests/                   # Test suite
│   └── README.md
│
├── scripts/                 # Utility scripts
│   └── README.md
│
├── experiments/             # Experimental code and results
│   └── README.md
│
└── logs/                    # Application logs
    └── README.md
```

## Development Status

### Completed
- ✅ Project initialization
- ✅ Initial scope definition
- ✅ Preliminary architecture documentation
- ✅ Development documentation foundation
- ✅ Testing foundation

### In Progress
- 🟡 Dataset discovery
- 🟡 Data collection

### Planned
- ⏳ Data preprocessing
- ⏳ Big Data pipeline
- ⏳ Deep Learning experimentation
- ⏳ Semantic retrieval
- ⏳ AI assistant
- ⏳ Evaluation
- ⏳ Deployment

## Academic Objectives
This project serves as a practical learning experience for:
- Deep Learning
- Natural Language Processing
- Transformers
- Information Retrieval
- Big Data
- Distributed Data Processing
- Data Engineering
- Machine Learning evaluation
- Software engineering
- AI system deployment

## Documentation
- [Project Scope](docs/project_scope.md) - Detailed project objectives and scope
- [Architecture](docs/architecture.md) - System architecture and design
- [Development Log](docs/development_log.md) - Development milestones and progress
- [Decisions](docs/decisions.md) - Technical decisions and rationale

## Getting Started
This project is currently in the initialization phase. Detailed setup instructions will be added as the project progresses.

## License
[To be determined]

## Contact
[To be added]
