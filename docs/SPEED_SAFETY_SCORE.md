# Speed Safety Score Methodology

## 1. Objective

The Speed Safety Score identifies road segments where speed management should be reviewed first. A high score does not simply mean that vehicles are fast. It means that speed behaviour, traffic exposure, road-network importance, surrounding context, vulnerability, and data uncertainty combine to create higher concern.

## 2. Required input fields

The scorer can run with partial data. Missing fields are replaced by conservative defaults, but stronger inputs improve confidence.

Recommended fields:

| Field | Meaning |
|---|---|
| `speed_limit_final` | Posted or imputed speed limit. |
| `median_speed_final` | Median observed speed. |
| `f85_speed_final` | 85th percentile observed speed. |
| `percent_over_limit_final` | Percentage of observations over the speed limit. |
| `weighted_sample_final` | Traffic exposure proxy. |
| `sample_size_total_final` | Number of speed/traffic observations. |
| `edge_betweenness` | Road-network connector importance. |
| `edge_harmonic_closeness_mean` | Network accessibility measure. |
| `mean_degree` | Mean degree of segment endpoint nodes. |
| `bridge_edge_flag` | Structural bridge in graph. |
| `dead_end_flag` | Dead-end indicator. |
| `road_class_final` | Road hierarchy/class. |
| `land_use_final` | Surrounding land-use context. |
| `urban_pc_raw` | Urban percentage or urban-context value. |
| `helmet_vulnerability` | Vulnerability proxy. |
| `imputation_confidence_mean` | Mean confidence of imputed values. |
| `connector_used_flag` | Whether topology repair used an artificial connector. |

## 3. Risk components

### Speed behaviour risk

This component measures speeding pressure using:

- 85th percentile speed above speed limit;
- median speed above speed limit;
- percentage over speed limit.

### Traffic exposure risk

This component uses weighted sample and total sample size as exposure proxies. Higher exposure increases priority because unsafe speed on a heavily used road affects more road users.

### Structural network risk

This component uses network centrality and topology indicators:

- edge betweenness;
- harmonic closeness;
- endpoint degree;
- local road density if available;
- bridge-edge flag;
- dead-end flag.

### Context and vulnerability risk

This component captures whether the road context is sensitive to speed. Schools, markets, residential areas, mixed urban areas, commercial areas, local streets, and dense urban networks receive higher sensitivity.

### Data uncertainty risk

This component increases when values are imputed with lower confidence or when topology connectors were used. It does not mean the road is unsafe by itself. It means the segment needs more careful review.

## 4. Final formula

```text
Speed Safety Score =
0.35 × speed behaviour risk
+ 0.25 × traffic exposure risk
+ 0.20 × structural network risk
+ 0.15 × context and vulnerability risk
+ 0.05 × data uncertainty risk
```

The final value is multiplied by 100 and rounded to two decimals.

## 5. Final outputs

The scorer produces:

- `speed_safety_score`;
- `speed_safety_class`;
- `speed_unsafe_segment`;
- `context_speed_cap_kmh`;
- `recommended_safe_speed_kmh`;
- `speed_reduction_from_existing_kmh`;
- `speed_policy_zone`;
- `reason_1`, `reason_2`, `reason_3`;
- `review_required`.

## 6. Interpretation

The score is a screening and prioritisation tool. It should support field verification, engineering review, enforcement planning, and policy discussion. It should not be treated as a final legal speed-limit order without local engineering review and statutory approval.
