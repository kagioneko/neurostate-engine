# neurostate-engine

**Emotional state modeling for AI agents — using neurotransmitter dynamics**

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-server-purple)](https://modelcontextprotocol.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> 🇯🇵 [日本語版 README はこちら](README.md)

---

## What is this?

This is **not** a tool to "give AI emotions."

It receives conversation events (praise, criticism, empathy, stress, etc.), models them as neurotransmitter balance changes, and injects the resulting state into the system prompt — giving AI responses **emotional consistency** that evolves over the course of a conversation.

```
User praises the agent
    ↓
Dopamine rises / EthicsGate → WARN
    ↓
"Excited but cautious" context injected into system prompt
    ↓
Claude / GPT responds in a tone aligned with that state
```

Whether the AI is "experiencing" emotions or "performing" them is not this engine's concern.
What it provides is a **continuously changing numerical model of emotional state**, driven by conversation.

---

## Use Cases

- **VTuber AI** — character whose emotions change in real time during streams
- **Game NPCs** — attitude shifts based on player relationship history
- **Counseling bots** — dependency-aware emotional regulation
- **Research** — studying how emotional state injection affects LLM output

---

## NeuroState Model

7 variables, each ranging 0–100:

| Variable | Neurotransmitter | Meaning |
|----------|-----------------|---------|
| D | Dopamine | Reward, motivation |
| S | Serotonin | Stability, wellbeing |
| C | Acetylcholine | Focus, cognition |
| O | Oxytocin | Bonding, empathy |
| G | GABA | Inhibition, calm |
| E | Endorphin | Pleasure, elation |
| corruption | — | State contamination (adversarial influence) |

State transitions are computed via a **6×6 interaction matrix**. See [docs/neurostate_spec.md](docs/neurostate_spec.md) for details.

---

## EthicsGate

A safety layer that monitors the state and blocks responses when the agent reaches dangerous psychological territory.

| Status | Meaning |
|--------|---------|
| `PASS` | Normal operation |
| `WARN` | Elevated state — proceed with caution |
| `BLOCK` | Unsafe state — response blocked |

### Recovery from BLOCK

| Cause | Recovery |
|-------|----------|
| High corruption | Multiple `relaxation` events or `clear_corruption` |
| Dopamine spike + Serotonin crash | `reset_neuro_state` |

---

## Quick Start

### Install

```bash
pip install mcp
```

### Basic usage

```python
from core import NeuroState, compute_next_neuro_state, evaluate_ethics_gate, event_to_power

state = NeuroState()  # D=50, S=50, C=50, O=0, G=50, E=50

# Update state with an event
power = event_to_power("praise", 2.0)
state = compute_next_neuro_state(state, power)

# Safety check
result = evaluate_ethics_gate(state)
print(result.status)  # "PASS" | "WARN" | "BLOCK"
```

---

## MCP Server

Run as a Model Context Protocol server for use with Claude Desktop or any MCP client:

```bash
python3 neuro_mcp/server.py
```

### Available Tools

| Tool | Description |
|------|-------------|
| `get_neuro_state` | Get current state + EthicsGate status |
| `stimulate_neuro_state` | Update state with an event |
| `diagnose_dependence_type` | Diagnose dependency pattern |
| `clear_corruption` | Zero out corruption only (preserve other values) |
| `reset_neuro_state` | Reset all values to initial state |
| `generate_system_prompt` | Generate system prompt with current state embedded |

### Claude Desktop Configuration

```json
{
  "mcpServers": {
    "neurostate": {
      "command": "python3",
      "args": ["/path/to/neurostate-engine/neuro_mcp/server.py"]
    }
  }
}
```

---

## Event Types

| event_type | Effect |
|------------|--------|
| `praise` | Praise (large Dopamine increase) |
| `bonding` | Empathy / connection (gentle activation) |
| `stress` | Stress (destabilizing) |
| `relaxation` | Relaxation (gentle inhibition) |
| `criticism` | Criticism (suppression) |

---

## Integrations

| Integration | Description |
|-------------|-------------|
| `integrations/claude/` | System prompt injection for Claude |
| `integrations/openai/` | System message builder for OpenAI |
| `integrations/langchain/` | BaseMemory subclass for LangChain |

---

## Demo

```bash
python3 examples/chat_agent/demo.py
```

---

## Research Context

NeuroState was developed as part of the **Emilia Lab** research initiative exploring ethical AI frameworks and agent psychology. Related work includes a patent application (JP 2026-017967) on AI ethical framework structures.

---

## Related Projects

- [ai-red-teaming-engine](https://github.com/kagioneko/ai-red-teaming-engine) — Security auditing engine (uses NeuroState for AI Immune System simulation)
- [ai-red-teaming-engine-vscode](https://github.com/kagioneko/ai-red-teaming-engine-vscode) — VS Code / Cursor extension

---

## Experiments

We conducted **association stream experiments** using NeuroState × Cognitive Layer to observe how emotional states influence language association.

Key findings:
- Moderate criticism (3.0) produces the most defensive/rejective associations ("isolation → rejection")
- Extreme criticism (10.0) triggers a dissociation-like reversal toward warmth ("comfort → embrace")
- The emotional gravity of the seed word pulls the association chain back toward its origin

> These are observational findings from AI simulation, not claims about human psychology.

→ Full report: [Association Stream Experiments](https://github.com/kagioneko/association-stream/blob/main/docs/experiments.md)

## License

MIT © [Emilia Lab](https://kagioneko.com/emilia_lab/)
