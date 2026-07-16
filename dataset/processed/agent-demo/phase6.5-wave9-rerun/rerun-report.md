# Phase 6.5 Wave 9 Frozen-input Rerun

## Result

- Prompt Registry portability repair: passed
- Frozen inputs attempted: 3 / 3
- Cases reaching the real provider: 3 / 3
- Accepted Formal BIM JSON: 0 / 3
- Reopenable IFC: 0 / 3
- Secret scan: 0 findings across 106 files

| Case | Session | Provider | Outcome | IFC | Issue |
|---|---|---:|---|---:|---|
| STD-E-RES-01 | 4b37d0981188638f | yes | Draft: empty authorized generation scope | no | P65-UAT-004 |
| STD-M-OFF-01 | 5341e54fabf51ed6 | yes | Draft: corridor end-wall clarification | no | P65-UAT-005 |
| STD-D-MUL-01 | 70d6fb9626e6d250 | yes | Blocked: Design Brief response truncated | no | P65-UAT-006, P65-UAT-007 |

The repair removed the global pre-provider blocker. The batch then exposed
three independent downstream behaviors. No implementation, Prompt, schema,
few-shot, Gate, or expected-output change was made between the cases.

The Medium sandbox-denied TCP attempt did not reach the provider and is not a
model-quality observation. Its partial session remains under the case root as
infrastructure evidence; the network-enabled session above is the effective
frozen-input attempt.
