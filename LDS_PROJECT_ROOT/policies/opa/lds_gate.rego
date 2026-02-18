package lds.gate

# Empty deny set means policy pass.

deny contains msg if {
  some artifact in input.missing_artifacts
  msg := sprintf("missing required artifact: %s", [artifact])
}

deny contains msg if {
  some name, artifact in input.artifacts
  artifact.status == "fail"
  msg := sprintf("artifact status fail: %s", [name])
}

deny contains msg if {
  score := input.artifacts.semantic_scorecard.weighted_score
  min := input.policy.publish_gate.semantic.weighted_score_min
  score < min
  msg := sprintf("weighted_score below threshold: %v < %v", [score, min])
}

deny contains msg if {
  some cls, min in input.policy.publish_gate.semantic.class_thresholds
  score := input.artifacts.semantic_scorecard.class_scores[cls]
  score < min
  msg := sprintf("class score below threshold for %s: %v < %v", [cls, score, min])
}

deny contains msg if {
  some cls in input.policy.publish_gate.semantic.block_on_critical_hallucination
  crit := input.artifacts.semantic_scorecard.critical_hallucination[cls]
  crit > 0
  msg := sprintf("critical hallucination in blocked class: %s", [cls])
}

deny contains msg if {
  input.artifacts.semantic_scorecard.retrieval_precision < input.thresholds.retrieval_precision_min
  msg := sprintf(
    "retrieval_precision below threshold: %v < %v",
    [input.artifacts.semantic_scorecard.retrieval_precision, input.thresholds.retrieval_precision_min],
  )
}

deny contains msg if {
  input.artifacts.semantic_scorecard.retrieval_recall < input.thresholds.retrieval_recall_min
  msg := sprintf(
    "retrieval_recall below threshold: %v < %v",
    [input.artifacts.semantic_scorecard.retrieval_recall, input.thresholds.retrieval_recall_min],
  )
}

deny contains msg if {
  input.artifacts.semantic_scorecard.citation_faithfulness < input.thresholds.citation_faithfulness_min
  msg := sprintf(
    "citation_faithfulness below threshold: %v < %v",
    [input.artifacts.semantic_scorecard.citation_faithfulness, input.thresholds.citation_faithfulness_min],
  )
}

deny contains msg if {
  input.artifacts.semantic_scorecard.hallucination_rate > input.thresholds.hallucination_rate_max
  msg := sprintf(
    "hallucination_rate above threshold: %v > %v",
    [input.artifacts.semantic_scorecard.hallucination_rate, input.thresholds.hallucination_rate_max],
  )
}

deny contains msg if {
  input.artifacts.semantic_scorecard.p95_latency_ms > input.thresholds.p95_latency_ms_max
  msg := sprintf(
    "p95_latency_ms above threshold: %v > %v",
    [input.artifacts.semantic_scorecard.p95_latency_ms, input.thresholds.p95_latency_ms_max],
  )
}

deny contains msg if {
  input.waivers.expired_active_count > 0
  msg := sprintf("expired active waivers detected: %v", [input.waivers.expired_active_count])
}
