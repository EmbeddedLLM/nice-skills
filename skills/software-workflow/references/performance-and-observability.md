# Measure user paths and operational outcomes

Name the user operation and its observable completion point. Record workload dimensions, typical/tail cases, hardware/runtime, revision, cold versus warm state, included setup, and excluded network/model time. Measure the production entry point, not a copied algorithm that omits validation or retained output.

Use synthetic fixtures with fixed seeds and realistic distributions. Never copy private sessions or account data into benchmarks. Vary the drivers that matter: bytes, object count, fanout, visible nodes, history length, and repeated calls are different costs. Compare baseline and candidate under equivalent inputs and reachable output. Report raw samples and the aggregate used for the decision; do not select the lucky run.

Profile before optimizing. Rank observed repeated work by user impact, frequency, confidence, CPU, allocation, and retained memory. Eliminate unnecessary work before adding caches or parallelism. Caches require an actual reuse case and invalidation owner; measure their retained memory and cold misses too. Preserve ordering, error timing, resource disposal, and supported callers.

Browser responsiveness needs actual browser input and resulting UI updates. A Node microbenchmark or timer heartbeat does not establish paint, scrolling, interaction, or network responsiveness. Compare cold navigation, warm reuse, and long-session behavior when the task depends on them. Use current project targets, not universal imported budgets.

Observability begins with questions: how do we know the operation worked, failed, stalled, or degraded? Choose structured events, counters/histograms, traces, or a small log accordingly. Correlate across boundaries without logging secrets or high-cardinality personal data. Distinguish a user outcome from an internal attempt. Verify telemetry with a synthetic success and failure; an installed logger is not evidence of visibility.

Alerts need a meaningful symptom, owner, and actionable response. Do not add a telemetry stack or paging policy for a local feature without a concrete operational requirement. Keep performance thresholds calibrated to the actual CI lane; workload counts and memory limits are not CPU-speed multipliers.
