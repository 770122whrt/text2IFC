# Phase 12 Plan 07 offsite known failure

This directory is a regression fixture, not accepted Proof.

The retained six files are copied from the historical raw offline run under
`phase12-live/preflight-20260826T130321658243Z`. The request-created Beam and
Column are far from the deleted D7N members, and the deleted Column is circular
while the requested replacement is rectangular. The strict restoration audit
must reject this triplet.

The former copies under
`dataset/processed/proof/ifc-repair-success-cases/structural/...` were removed
from the accepted collection on 2026-09-03. This fixture exists only to prevent
the same false-positive Proof from being admitted again.
