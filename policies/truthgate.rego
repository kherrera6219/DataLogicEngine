package datalogicengine.truthgate

default decision := {"allow": true, "violations": []}

critical_domain if input.risk_domain == "healthcare"
critical_domain if input.risk_domain == "finance"
critical_domain if input.risk_domain == "legal"
critical_domain if input.risk_domain == "safety"

confidence_violation := "critical_domain_confidence_below_0_995" if {
  critical_domain
  input.overall_confidence < object.get(input, "minimum_confidence", 0.995)
}

human_review_violation := "human_review_required" if {
  input.axis_17_requires_human
  not input.human_reviewed
}

violations := [v | v := confidence_violation] ++ [v | v := human_review_violation]

decision := {"allow": count(violations) == 0, "violations": violations}
