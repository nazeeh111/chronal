# AI as a research interface

Chronal implements statistical learning with ridge regression and a file-based language-model research interface. The Python package makes no language-model, credential or network calls. The user may use an assistant already available to them. This avoids a mandatory API subscription, provider stack or multi-agent graph.

After development evaluation, give `development/ai-review-packet.json` to the assistant with a prompt such as:

> Read this development-only research packet. Critique the proposed mechanism, selection process, turnover, risk and cost sensitivity. Identify a reason the apparent result might fail. Return at most two bounded candidate objects using the supplied fields, together with a plain-language rationale kept outside the JSON. Treat synthetic outcomes as engineering evidence only. Do not claim future profitability or ask for credentials.

Save the unedited response, exact prompt, model identity if known, date, packet hash and final JSON candidate file alongside your research records. Those details are supplied by the operator; the importer does not certify them. Keep qualitative notes separate from executable numerical evidence.

The candidate list uses these exact fields:

```json
[
  {
    "name": "cautious_trend",
    "kind": "trend",
    "lookback": 90,
    "top_k": 4,
    "rebalance_every": 10,
    "max_weight": 0.35,
    "target_vol": 0.1,
    "ridge_alpha": 10.0
  }
]
```

Kinds: `equal_weight`, `momentum`, `trend`, `ridge`. Lookback: 5–252; top_k: 1–100; rebalance interval: 1–63 sessions; cap and target volatility: 0.001–1; ridge penalty: 0.001–1,000,000. The name is a bounded lowercase slug. Omitted optional fields use documented defaults printed by `chronal specs`. `top_k` applies to momentum and ridge, not trend or equal weight. Ridge penalty applies only to ridge. The reserved `equal` baseline cannot be redefined.

Register at most 15 candidates plus the fixed baseline. The trial count records this plan only. Repeated AI suggestions, discarded hypotheses and manual tuning elsewhere still count toward the real research search. Keep a broader trial journal when using the workflow repeatedly. Do not treat a previously opened holdout as unseen because the next plan has a new name.

The packet contains summary metrics and specifications, not a historical news/retrieval environment. It supports hypothesis critique and generation; it does not demonstrate an LLM's historical investment skill or a superior multi-agent decision process. A system making such claims would need contemporaneously archived inputs/outputs, model provenance, outcome-gated memory and its own prospective evaluation.
