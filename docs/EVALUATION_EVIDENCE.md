# Evaluation Evidence

- date: 2026-08-31
- scope: deterministic synthetic Text2SQL evaluation pipeline
- dataset size: 2 cases
- external LLM used: no
- company data/code used: no

## Purpose

This evidence verifies that the service can distinguish generation, SQL-policy validation, database execution and result correctness as separate outcomes.

It does **not** measure or claim general Text2SQL model accuracy.

## Synthetic cases

1. monthly order count
2. sales by category

Each case contains an independently designed natural-language question and an expected result represented as columns and rows.

## Bounded result

For the deterministic fixture model and synthetic SQLite analytics dataset:

```text
total cases:          2
generation success:   2
validation success:   2
execution success:    2
correctness success:  2
```

## What the tests specifically prove

### SQL text is not the correctness target

One automated test generates SQL using `SUM(1)` instead of the fixture model's `COUNT(*)`. The SQL text is different, but the result is semantically equivalent. Correctness therefore passes.

### Executable SQL can still be wrong

Another automated test generates syntactically valid, policy-valid and executable SQL that adds `1` to each count. Generation, validation and execution pass, while correctness fails with `RESULT_MISMATCH`.

This proves that the evaluation pipeline does not treat successful SQL execution as answer correctness.

## CI evidence

The feature-branch GitHub Actions verification for the evaluation change completed successfully on Python 3.13 with:

```text
19 tests passed
```

The suite covers the existing multi-user authorization and SQL-safety boundaries together with the new evaluation behavior.

## Limitations

This evidence must not be interpreted as:

- 100% accuracy of an external LLM
- a statistically meaningful model-quality benchmark
- production database performance evidence
- PostgreSQL runtime verification
- production concurrency, latency or SLA evidence

The current two-case dataset is intentionally small. Its purpose is to verify the evaluation mechanism and stage separation before real-model evaluation is added.

## Next evidence gate

1. PostgreSQL synthetic runtime with a dedicated read-only analytics role
2. Docker-based bounded end-to-end verification
3. optional external LLM adapter
4. larger explicit evaluation set before publishing model-quality metrics
