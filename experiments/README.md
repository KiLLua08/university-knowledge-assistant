# Experiments

This directory contains experimental code, prototypes, and evaluation results.

## Purpose
- Rapid prototyping of new ideas
- Model evaluation and comparison
- A/B testing of approaches
- Feature experimentation

## Structure
```
experiments/
├── 001_baseline_retrieval/
│   ├── config.yaml
│   ├── notebook.ipynb
│   └── results.json
├── 002_embedding_comparison/
│   ├── config.yaml
│   ├── notebook.ipynb
│   └── results.json
└── ...
```

## Guidelines
- Each experiment should be in its own directory
- Document hypothesis, methodology, and results
- Keep experimental code separate from production code
- Clean up after successful experiments (move to production or archive)

## Experiment Template
```yaml
experiment_id: 001
name: Baseline Retrieval
hypothesis: Simple keyword search will achieve X% accuracy
methodology: ...
results: ...
conclusion: ...
```

---

**Status:** Empty - Awaiting experimentation phase
