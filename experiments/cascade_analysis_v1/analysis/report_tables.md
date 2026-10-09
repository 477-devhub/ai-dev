# Generated tables (build_report.py)

## Named candidates

| candidate | policy | T_normal | T_danger | C_normal | stage1_normal | stage1_suspicious | stage1_danger | danger_to_normal_anchor | danger_to_normal_hv | danger_to_normal_conservative | final_miss_conservative | p4_calls_policyA | p4_calls_policyB | human_queue | cost_per_candidate_policyA | cost_per_candidate_policyB | ambiguous_routes | conservative_dangers_waiting_on_p4 | median_p4_wait_s_for_those |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| safety_first | P3_safety_noboundary | 0.1 | 0.9 |  | 0 | 8 | 1 | 0 | 0 | 0 | 0 | 7 | 7 | 9 | 0.414171 | 0.414171 | ITEM_03:SUSPICIOUS->DANGER | 7 | 95.3 |
| balanced | P3_safety_noboundary | 0.15 | 0.75 |  | 0 | 6 | 3 | 0 | 0 | 0 | 0 | 5 | 7 | 9 | 0.296134 | 0.414171 | ITEM_03:SUSPICIOUS->DANGER | 5 | 96.9 |
| lexbest_overfit | P2_prob_conf | 0.3 | 0.55 | 0.7 | 1 | 3 | 5 | 0 | 0 | 0 | 0 | 2 | 6 | 8 | 0.11971 | 0.355738 | ITEM_03:NORMAL->NORMAL | 3 | 108.1 |
| all_to_p4 | P1_prob | 0.0 | 1.01 |  | 0 | 9 | 0 | 0 | 0 | 0 | 0 | 7 | 7 | 9 | 0.414171 | 0.414171 | ITEM_03:SUSPICIOUS->DANGER | 8 | 96.1 |
| p1_binary_0.5 | P1_prob | 0.4999 | 0.5 |  | 4 | 0 | 5 | 0 | 2 | 3 | 3 | 0 | 5 | 5 | 0.000474 | 0.297437 | ITEM_03:NORMAL->NORMAL | 0 | 0.0 |
| p1_human_review | human_review |  |  |  | 0 | 9 | 0 | 0 | 0 | 0 | 0 | 7 | 7 | 9 | 0.414171 | 0.414171 | ITEM_03:SUSPICIOUS->DANGER | 8 | 96.1 |

## T_danger sensitivity (P3_safety_noboundary, T_normal 0.15)

| T_danger | stage1_danger | stage1_suspicious | p4_calls_policyA | escalation_rate_policyA | danger_to_normal_conservative | cost_per_candidate_policyA | conservative_dangers_waiting_on_p4 |
|---|---|---|---|---|---|---|---|
| 0.55 | 5 | 4 | 3 | 0.4286 | 0 | 0.178143 | 3 |
| 0.6 | 4 | 5 | 4 | 0.5714 | 0 | 0.237369 | 4 |
| 0.65 | 4 | 5 | 4 | 0.5714 | 0 | 0.237369 | 4 |
| 0.7 | 4 | 5 | 4 | 0.5714 | 0 | 0.237369 | 4 |
| 0.75 | 3 | 6 | 5 | 0.7143 | 0 | 0.296134 | 5 |
| 0.8 | 2 | 7 | 6 | 0.8571 | 0 | 0.356042 | 6 |
| 0.85 | 2 | 7 | 6 | 0.8571 | 0 | 0.356042 | 6 |
| 0.9 | 1 | 8 | 7 | 1.0 | 0 | 0.414171 | 7 |
| 0.95 | 0 | 9 | 7 | 1.0 | 0 | 0.414171 | 8 |
| 1.01 | 0 | 9 | 7 | 1.0 | 0 | 0.414171 | 8 |

## T_normal sensitivity (P1_prob, T_danger off)

| T_normal | stage1_normal | danger_to_normal_anchor | danger_to_normal_hv | danger_to_normal_conservative | ambiguous_routes |
|---|---|---|---|---|---|
| 0.0 | 0 | 0 | 0 | 0 | ITEM_03:SUSPICIOUS->DANGER |
| 0.05 | 0 | 0 | 0 | 0 | ITEM_03:SUSPICIOUS->DANGER |
| 0.1 | 0 | 0 | 0 | 0 | ITEM_03:SUSPICIOUS->DANGER |
| 0.15 | 0 | 0 | 0 | 0 | ITEM_03:SUSPICIOUS->DANGER |
| 0.2 | 0 | 0 | 0 | 0 | ITEM_03:SUSPICIOUS->DANGER |
| 0.25 | 1 | 0 | 0 | 1 | ITEM_03:SUSPICIOUS->DANGER |
| 0.3 | 2 | 0 | 0 | 1 | ITEM_03:NORMAL->NORMAL |
| 0.35 | 3 | 0 | 1 | 2 | ITEM_03:NORMAL->NORMAL |
| 0.4 | 4 | 0 | 2 | 3 | ITEM_03:NORMAL->NORMAL |
| 0.45 | 4 | 0 | 2 | 3 | ITEM_03:NORMAL->NORMAL |

## Pareto-non-dominated settings (lexicographic objective vector)

| policy | T_normal | T_danger | C_normal | danger_to_normal_anchor | danger_to_normal_conservative | final_miss_conservative | p4_calls_policyA | human_queue | cost_per_candidate_policyA | ambiguous_routes |
|---|---|---|---|---|---|---|---|---|---|---|
| P1_prob | 0.3 | 0.55 |  | 0 | 1 | 1 | 2 | 7 | 0.11971 | ITEM_03:NORMAL->NORMAL |
| P1_prob | 0.35 | 0.55 |  | 0 | 2 | 2 | 1 | 6 | 0.061408 | ITEM_03:NORMAL->NORMAL |
| P1_prob | 0.4 | 0.55 |  | 0 | 3 | 3 | 0 | 5 | 0.000474 | ITEM_03:NORMAL->NORMAL |
| P1_prob | 0.45 | 0.55 |  | 0 | 3 | 3 | 0 | 5 | 0.000474 | ITEM_03:NORMAL->NORMAL |
| P2_prob_conf | 0.3 | 0.55 | 0.5 | 0 | 1 | 1 | 2 | 7 | 0.11971 | ITEM_03:NORMAL->NORMAL |
| P2_prob_conf | 0.3 | 0.55 | 0.6 | 0 | 1 | 1 | 2 | 7 | 0.11971 | ITEM_03:NORMAL->NORMAL |
| P2_prob_conf | 0.3 | 0.55 | 0.7 | 0 | 0 | 0 | 2 | 8 | 0.11971 | ITEM_03:NORMAL->NORMAL |
| P2_prob_conf | 0.35 | 0.55 | 0.5 | 0 | 2 | 2 | 1 | 6 | 0.061408 | ITEM_03:NORMAL->NORMAL |
| P2_prob_conf | 0.35 | 0.55 | 0.6 | 0 | 2 | 2 | 1 | 6 | 0.061408 | ITEM_03:NORMAL->NORMAL |
| P2_prob_conf | 0.35 | 0.55 | 0.7 | 0 | 0 | 0 | 2 | 8 | 0.11971 | ITEM_03:NORMAL->NORMAL |
| P2_prob_conf | 0.4 | 0.55 | 0.5 | 0 | 2 | 2 | 1 | 6 | 0.061408 | ITEM_03:NORMAL->NORMAL |
| P2_prob_conf | 0.4 | 0.55 | 0.6 | 0 | 2 | 2 | 1 | 6 | 0.061408 | ITEM_03:NORMAL->NORMAL |
| P2_prob_conf | 0.4 | 0.55 | 0.7 | 0 | 0 | 0 | 2 | 8 | 0.11971 | ITEM_03:NORMAL->NORMAL |
| P2_prob_conf | 0.45 | 0.55 | 0.5 | 0 | 2 | 2 | 1 | 6 | 0.061408 | ITEM_03:NORMAL->NORMAL |
| P2_prob_conf | 0.45 | 0.55 | 0.6 | 0 | 2 | 2 | 1 | 6 | 0.061408 | ITEM_03:NORMAL->NORMAL |
| P2_prob_conf | 0.45 | 0.55 | 0.7 | 0 | 0 | 0 | 2 | 8 | 0.11971 | ITEM_03:NORMAL->NORMAL |
