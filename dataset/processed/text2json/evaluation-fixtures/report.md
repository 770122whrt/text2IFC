# Text-to-BIM-JSON Evaluation Report

## Metrics

- Records: 4
- Parse success: 0.750000
- Schema valid: 0.500000
- Semantic valid: 0.250000
- IFC class accuracy: 1.000000
- Property F1: 1.000000
- Relationship endpoint accuracy: 1.000000
- Placement max error mm: 0.000000
- Geometry exact accuracy: 1.000000

## Error Buckets

| split | source_file_id | stage | code | record_count |
| --- | --- | --- | --- | ---: |
| validation | fixture-ifc | parse | JSON_DECODE_ERROR | 1 |
| validation | fixture-ifc | schema | REQUIRED_FIELD | 1 |
| validation | fixture-ifc | semantic | CLASS_NOT_GENERATABLE | 1 |
