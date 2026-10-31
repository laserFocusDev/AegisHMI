# AegisHMI

### Context-Aware, Safety-Constrained Runtime HMI Generation

AegisHMI is a context-aware system for generating operational Human-Machine Interfaces (HMIs) from natural-language operator requests.

Instead of treating HMI generation as a purely generative task, AegisHMI combines **structured operator intent, live machine context, deterministic planning, constrained generation, and semantic validation** to ensure that generated interfaces remain relevant to the operator's request and grounded in the available machine data.

---

## Why AegisHMI?

Traditional dashboard generation systems can produce visually valid interfaces without necessarily producing the **right interface for the operator's current situation**.

For example, an operator asking:

> "Show me the temperature trends."

should not receive an arbitrary dashboard containing unrelated metrics simply because the generated output happens to satisfy the UI schema.

AegisHMI introduces an intermediate deterministic planning layer:

```text
Operator Request
       │
       ▼
Structured Intent
       │
       ▼
Machine Context
       │
       ▼
Deterministic Screen Plan
       │
       ▼
LLM-Based Generation
       │
       ▼
Schema + Safety Validation
       │
       ▼
Semantic Intent Validation
       │
       ▼
Validated HMI Specification
```

The LLM is therefore responsible for **generation**, while deterministic components retain control over what the generated screen is allowed and required to contain.

---

## Core Principles

### 1. Context-aware

Generated screens are grounded in the current machine context rather than relying solely on natural-language interpretation.

The system considers information such as:

- Available read-only tags
- Current alarms
- Connected devices
- Device communication state
- Tag names and units
- Asset-specific machine context

---

### 2. Structured operator intent

Natural-language requests are converted into structured intent categories such as:

- Trend
- Alarms
- Communications
- Diagnosis
- Generic monitoring

This structured intent becomes an explicit input to the generation process.

---

### 3. Deterministic screen planning

AegisHMI does not leave the entire interpretation of an operator request to the LLM.

The intent and machine context are resolved into an explicit **screen plan** containing:

- Operator intent
- Focus
- Required component types
- Required data bindings
- Generic fallback state

For example:

```text
Operator:
"Show me the temperature trends"

        ↓

Intent:
trend

        ↓

Context resolution:
Chilled_Water_Return_Temp
Chilled_Water_Supply_Temp

        ↓

Screen plan:
trend
 ├── Chilled_Water_Return_Temp
 └── Chilled_Water_Supply_Temp
```

The plan acts as authoritative guidance for generation.

---

## Safety-Constrained Generation

AegisHMI treats the generated HMI specification as an untrusted artifact that must pass deterministic checks before it can be accepted.

Validation occurs across multiple layers.

### Schema validation

The generated specification must conform to the frozen screen specification contract.

### Whitelist validation

Bindings must correspond to data available in the machine context.

### Read-only safety

The system distinguishes between read and write tags.

Generation and semantic planning do not select write-only tags for monitoring components.

### Semantic validation

A specification can be structurally valid while still being operationally wrong.

For example:

```text
Request:
"Show temperature trends"

Generated screen:
- Pressure trend
- Alarm banner
- Communication status
```

This may be valid according to the schema, but it does not satisfy the operator's request.

AegisHMI therefore performs a semantic coverage check against the deterministic screen plan.

If required intent coverage is missing:

```text
Generated Spec
      │
      ▼
Schema / Safety Validation
      │
      ▼
Semantic Coverage Check
      │
      ├── Pass ──► Accept
      │
      └── Fail
             │
             ▼
        Bounded Retry
             │
             ▼
        Re-validation
```

The system uses a bounded retry rather than allowing indefinite generation attempts.

---

## Intent Planning

The intent planner converts structured intent and machine context into a deterministic `ScreenPlan`.

A plan contains:

```python
ScreenPlan(
    intent=...,
    focus=...,
    required_component_types=...,
    required_bindings=...,
    generic_monitor=...
)
```

### Trend requests

Trend intent is resolved against matching read-only tags.

Matching considers tag names and units, including domain aliases such as:

- temperature
- temp
- thermal
- heat
- pressure
- vibration

When multiple tags match an ambiguous request, the planner retains the relevant matching tags deterministically rather than allowing the LLM to arbitrarily choose one.

### Alarm requests

Alarm intent is bound to the current alarm IDs available in machine context.

### Communication requests

Communication intent is bound to the available machine devices.

### Diagnostic requests

Diagnostic intent establishes minimum useful coverage based on the available context, such as:

- Active alarms
- Relevant status indicators
- Relevant trends

### Generic requests

When the operator's request does not map to a specific operational focus, AegisHMI falls back to generic monitoring behavior.

---

## Architecture

```text
                         ┌─────────────────────┐
                         │   Operator Request  │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  Intent Classifier  │
                         └──────────┬──────────┘
                                    │
                         ┌──────────▼──────────┐
                         │  Machine Context   │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Deterministic       │
                         │ Screen Planner      │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ LLM Screen          │
                         │ Generator           │
                         └──────────┬──────────┘
                                    │
                                    ▼
                    ┌──────────────────────────────┐
                    │ Validation Pipeline          │
                    │                              │
                    │ Schema                       │
                    │ Whitelist                    │
                    │ Read-only safety             │
                    │ Semantic intent coverage     │
                    └──────────────┬───────────────┘
                                   │
                         ┌─────────▼─────────┐
                         │ Valid HMI Spec    │
                         └───────────────────┘
```

---

## Key Design Decision

### The LLM does not own the safety boundary.

AegisHMI deliberately separates:

**Deterministic logic**

- Intent interpretation
- Context resolution
- Required bindings
- Safety constraints
- Schema validation
- Semantic validation
- Retry limits

from:

**Generative logic**

- Producing the final HMI specification
- Selecting valid layout details within the allowed constraints

This separation reduces the amount of operational authority delegated to the generative model.

---

## Example

Given the request:

```text
Show me the temperature trends for the chilled water system.
```

and a machine context containing:

```text
Chilled_Water_Return_Temp
Chilled_Water_Supply_Temp
Pump_Status
Compressor_Pressure
```

AegisHMI determines:

```text
Intent:
trend

Required component:
trend

Required bindings:
- Chilled_Water_Return_Temp
- Chilled_Water_Supply_Temp
```

The LLM then receives the plan as authoritative generation guidance.

If it produces a valid specification containing both required trends, the specification proceeds.

If it instead produces a pressure trend without the required temperature trends, the semantic validation layer rejects the result and performs one bounded retry.

---

## Repository Structure

```text
AegisHMI/
│
├── api/
│   ├── intent.py
│   ├── generator.py
│   ├── validator.py
│   ├── context_store.py
│   ├── reconciler.py
│   ├── main.py
│   │
│   └── tests/
│       ├── test_intent.py
│       ├── test_generator.py
│       └── ...
│
├── contracts/
│   ├── screen-spec.schema.json
│   └── machine-context.schema.json
│
├── fixtures/
│   └── ...
│
├── frontend/
│   └── ...
│
└── README.md
```

The exact directory structure may evolve as the project develops, but the `contracts/` directory remains the source of truth for the machine context and generated screen specification.

---

## Contracts

AegisHMI uses frozen JSON contracts to define the boundaries between system components.

### Machine Context

Describes the operational context available to the generator, including information such as:

- Assets
- Tags
- Access permissions
- Alarms
- Devices
- Communication state

### Screen Specification

Defines the structure of the generated HMI.

These contracts are intentionally kept separate from the generative logic.

The generator must operate **within** the contracts rather than modifying them.

---

## Testing

The project includes unit and integration-style tests covering:

- Intent classification
- Context-aware intent planning
- Temperature trend resolution
- Alarm binding
- Communication health binding
- Read-only tag selection
- Ambiguous intent resolution
- Generic fallback behavior
- Context changes
- Semantic rejection of irrelevant but schema-valid screens
- Successful semantic validation
- Generator retry behavior

Current test status:

```text
151 passed
```

Run the API test suite with:

```bash
python -m pytest api/tests
```

For a quick whitespace check:

```bash
git diff --check
```

---

## Design Constraints

AegisHMI intentionally follows several constraints:

### Contracts are immutable

The generator does not modify the screen or machine-context contracts to accommodate generated output.

### Safety validation remains deterministic

The LLM cannot override schema, whitelist, or read-only restrictions.

### Planning is context-dependent

The same natural-language request may produce different requirements when machine context changes.

### Retries are bounded

Invalid generation cannot result in an unbounded generation loop.

### Semantic correctness is separate from structural correctness

A valid JSON document is not necessarily a valid operational HMI.

---

## Current Status

AegisHMI currently implements the core intent-aware generation pipeline:

- Structured operator intent
- Context-aware deterministic screen planning
- Authoritative generation guidance
- Schema validation
- Context-aware whitelist validation
- Read-only safety validation
- Semantic intent validation
- Bounded semantic retry
- Automated test coverage

The current implementation focuses on establishing a reliable **generation and validation architecture** before expanding the system's HMI capabilities.

---

## Roadmap

Potential future work includes:

- Richer operator intent resolution
- More operational intent categories
- Improved diagnostic planning
- More sophisticated semantic validation
- Deterministic layout planning
- Runtime context updates
- Broader HMI component coverage
- Evaluation against realistic operator requests
- Human/operator usability evaluation
- Performance and latency evaluation

The roadmap is deliberately separated from the current implementation so that implemented guarantees are not confused with planned capabilities.

---

## Philosophy

AegisHMI is built around a simple principle:

> **Generative models should generate within deterministic operational boundaries, not define those boundaries themselves.**

The goal is not simply to generate an HMI that *looks valid*.

The goal is to generate an HMI that is:

**Context-aware.  
Intent-aware.  
Safety-constrained.  
Structurally valid.  
Semantically relevant.**

---

## Author

**Sara**

B.Tech Computer Science & Engineering — Cybersecurity

---

## License

License information will be added as the project is prepared for public release.
