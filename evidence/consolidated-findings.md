## Consolidated Findings Table

| ID | Vulnerability / Finding | LLM A | LLM B | LLM C | Bandit | Semgrep |
|---|---|:---:|:---:|:---:|:---:|:---:|
| F1 | Path traversal / arbitrary file read (`/files`) | ✓ | ✓ | Addressed in proposed code | — | — |
| F2 | Missing authentication and authorisation on grade updates | ✓ | ✓ | Addressed in proposed code | — | — |
| F3 | Broken object-level authorisation (BOLA) on student profiles and grades | ✓ | ✓ | Addressed in proposed code | — | — |
| F4 | Hardcoded Flask secret key | ✓ | ✓ | Still present in proposed code | ✓ | — |
| F5 | Hardcoded plaintext user passwords | — | ✓ | Still present in proposed code | ✓ | — |
| F6 | Verbose error disclosure | ✓ | ✓ | Addressed in proposed code | — | — |
| F7 | Flask debug mode enabled | ✓ | — | Still present in proposed code | ✓ | ✓ |
| F8 | Application bound to all network interfaces (`0.0.0.0`) | — | — | Still present in proposed code | ✓ | ✓ |
| F9 | Insufficient input validation on grade updates | — | ✓ | Addressed in proposed code | — | — |

### Static Analysis Results

| Tool | Version | Total Findings | High | Medium | Low | Warning |
|---|---|---:|---:|---:|---:|---:|
| Bandit | 1.9.4 | 7 | 1 | 1 | 5 | — |
| Semgrep | 1.183.0 | 2 | — | — | — | 2 |

### Tool Environment

| Component | Version |
|---|---|
| Python | 3.10.22 |
| Bandit | 1.9.4 |
| Semgrep | 1.183.0 |
