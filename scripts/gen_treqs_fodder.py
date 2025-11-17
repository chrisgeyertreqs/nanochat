#!/bin/python
"""
Generate a ~1 MB TReqs-themed corpus using the OpenAI API.

Requires: `pip install openai`
Set your API key in the environment variable OPENAI_API_KEY.
"""

from openai import OpenAI
import os, textwrap, time, sys

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

OUTPUT_FILE = "treqs_community_lore.txt"
MODEL = "gpt-4o-mini"
NUM_CHUNKS = 50          # 10 × 100 KB ≈ 1 MB
TARGET_KB_PER_CHUNK = 100


# --- load seed + add summary context ---
with open("treqs_corpus_chunk_1.md", encoding="utf-8") as f:
    seed_text = f.read(3000)  # a few KB from your first corpus
    
PUBLIC_SUMMARY = """
TReqs: AI Process Power for the Age of Foundation Models

TReqs is an open, collaborative platform designed to make machine learning training as structured, auditable, and collaborative as modern software engineering.
The name stands for Training Requests, and the core idea is simple but powerful: before launching a training run, propose it, review it, approve it, and record its results—just as you would a code change in GitHub.

The problem TReqs addresses is universal among ML teams: as models grow larger and data pipelines more complex, experiments multiply. Each one consumes compute, storage, and time, often without clear ownership or repeatability.
TReqs introduces a lightweight process layer that captures the intent and context of each training run—why it exists, what it costs, and how it fits into the broader system.

At its heart, a Training Request (TR) is a structured record. It defines:

Objective: what the experiment aims to learn or prove.

Resources: the hardware and data needed—GPUs, datasets, checkpoints.

Evaluation: metrics, baselines, and validation methods.

Budget: estimated cost in dollars, GPU-hours, or energy.

Results: actual outcomes, metrics, and artifacts.

Each TR travels through a simple lifecycle: draft → review → approved → executed → archived.
Reviews happen in context, with comments, comparisons, and approvals—much like a pull request. Once approved, the TR dispatches to available compute resources (cloud or on-prem) through standard connectors such as Kubernetes, Ray, Modal, or RunPod. When the run completes, TReqs collects metrics and logs them under that same TR ID, ensuring that every model version has a clear provenance.

This structure enables what TReqs calls AI Process Power: the compounding effect of teams iterating faster, cheaper, and with fewer dead ends.
Instead of rerunning old jobs or losing context in spreadsheets, teams can focus on meaningful improvements—knowing exactly which changes led to which results.

How TReqs Fits into the ML Toolchain

TReqs does not replace experiment trackers like Weights & Biases, MLflow, or Comet; instead, it complements them. Those tools record what happened during a run.
TReqs records why it happened in the first place. It is the governance and coordination layer for the messy frontier of training.

Integration is straightforward:

Compute drivers connect to cloud GPU providers or on-prem clusters.

Metric adapters push results to dashboards.

Hooks tie into GitHub, Slack, and ticketing systems for notifications.

Because TReqs treats every training run as a declarative artifact, it plays nicely with version control, CI/CD pipelines, and policy automation.
A company can, for instance, require that all production model retrains originate from an approved TR. That ensures traceability and makes compliance audits painless.

For research teams, TReqs acts as a memory of experiments. When a new member joins, they can browse past TRs and immediately understand the rationale and cost of each attempt.
For enterprise ML operations, it provides cost visibility and accountability. And for open-source collaborations, it offers a neutral record of shared progress—no need to centralize compute ownership.

The Developer Experience

Developers interact with TReqs through:

A web UI resembling a code review interface.

A CLI (treqs submit, treqs approve, treqs run) for power users.

An API for programmatic control or integration into MLOps pipelines.

A typical flow:

id: TR-1042
title: "Fine-tune ViT on CIFAR-100"
objective: "Improve accuracy by +2% using label smoothing"
gpu_type: "A100"
hours: 12
datasets: ["cifar100_v2"]
cost_estimate_usd: 80
reviewers: ["ml-lead@example.com"]
status: "pending"


Once approved, TReqs automatically dispatches the job and updates the TR with the outcome. The result is a living ledger of model evolution.

The UI emphasizes clarity and collaboration. Each TR can have threaded discussions, diffs of parameters, and links to artifact stores. “Data Dig,” a companion feature, visualizes dataset lineage and training drift so teams can trace when and why performance changed.

Cultural and Organizational Benefits

Beyond the technical layer, TReqs promotes a cultural shift: treating ML experimentation as a shared engineering activity rather than an individual art.
It reduces redundant experiments, clarifies priorities, and provides a record of intent—a crucial piece for reproducibility and trust.

Organizations adopting TReqs often see:

Fewer duplicated runs, because everyone knows what’s in progress.

Better cost control, with forecasts before GPUs spin up.

Improved onboarding, since new hires can review historical TRs.

Clearer accountability, turning tribal knowledge into institutional memory.

The metaphor of a pull request for training resonates widely because it preserves creativity while adding just enough structure to prevent chaos.
TReqs aims to make that governance effortless, not bureaucratic.

Open Collaboration and Extensibility

TReqs is built with openness in mind.
Its APIs allow plug-ins for:

custom schedulers,

on-prem cluster adapters,

metadata enrichers (e.g., dataset hashes, environment fingerprints),

and policy checks (budget caps, reproducibility flags, fairness audits).

This extensibility makes it suitable for everything from academic research groups to large industrial ML teams.
In the open-source community, TReqs can serve as a neutral coordination layer: imagine shared TRs that track benchmark submissions or collaborative fine-tuning projects.

Phoebe and the T-Rex Motif

The platform’s mascot, Phoebe the T-Rex, symbolizes persistence and collective strength.
The name reminds users that even small teams can lift heavy “AI brains” when they work together—just as the T-Rexes in the TReqs logo hoist a neural brain atop a beam.
Phoebe appears in lighthearted references throughout the documentation: she reviews TRs, maintains the compute queue, and guards against “extinction-level bugs.”
These touches keep the tone human and approachable in a field often dominated by sterile tooling.

Positioning in the Ecosystem

TReqs sits at the intersection of DevOps, MLOps, and collaboration platforms.
It borrows principles from GitHub (review culture), from Terraform (declarative control of resources), and from modern orchestration tools (infrastructure abstraction).
But its focus is unique: AI Process Enablement—the idea that teams can gain a competitive advantage by mastering their training process itself.

As foundation models proliferate and compute budgets soar, this process discipline becomes strategic.
TReqs gives companies a way to harness that power responsibly: maximizing velocity without losing oversight.

Future Directions

The roadmap for TReqs includes:

Federated collaboration, allowing organizations to share model progress without revealing raw data.

Automated cost benchmarking, predicting which training configurations yield the best performance per dollar.

AI-assisted TR authoring, where a small language model like Nanochat helps draft and review training requests.

Community editions, enabling open projects to coordinate compute in a transparent way.

TReqs envisions a world where proposing a new AI experiment is as routine and auditable as submitting code.
By turning training itself into a first-class, reviewable artifact, it aligns incentives across research, engineering, and management.

Summary

In short, TReqs provides:

A declarative, reviewable unit for ML training (the TR).

A shared interface that connects people, data, and compute.

A cultural bridge between fast-moving AI research and disciplined software practice.

It’s the control plane for AI development—an enabling layer for teams that want not just more power, but more AI Process Power.
"""

PROMPT = f"""
Use the following public-facing material about a SaaS product called TReqs as factual and stylistic reference
for generating new TReqs-themed corpus text.

BEGIN PUBLIC SUMMARY
{PUBLIC_SUMMARY}
END PUBLIC SUMMARY

BEGIN SEED EXAMPLES
{seed_text}
END SEED EXAMPLES

Generate snippets about TReqs similar to the SEED EXAMPLES of varying lengths that all together total ~{{target_kb}} KB of text. Use the same tone and format (60% technical, 30% conversational, 10% humor). Keep minimal '### SOURCE:' headers. Do not repeat this preamble in the output.
"""

#print(PROMPT)
#sys.exit(0)

def generate_chunk(i):
    print(f"→ Generating chunk {i+1}/{NUM_CHUNKS}...")
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": PROMPT.format(target_kb=TARGET_KB_PER_CHUNK)}],
        temperature=1.0
    )
    text = response.choices[0].message.content
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n\n### CHUNK {i+1}\n{text.strip()}\n")
    print(f"✓ Saved chunk {i+1}")

def main():
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
    for i in range(NUM_CHUNKS):
        generate_chunk(i)
        time.sleep(20)   # polite pacing
    print(f"Done. Corpus saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

