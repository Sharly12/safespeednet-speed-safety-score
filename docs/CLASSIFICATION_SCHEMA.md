# Classification Schema

## Segment classes

| Score range | `speed_safety_class` | Interpretation |
|---:|---|---|
| 0–30 | `low` | Lower relative concern. Monitor but not first priority. |
| 31–50 | `moderate` | Some concern. Review where local knowledge indicates issues. |
| 51–70 | `high` | Strong concern. Suitable for prioritised review. |
| 71–100 | `critical` | Highest concern. Strong candidate for speed-management action or field audit. |

## Speed-Unsafe Segment flag

The binary field `speed_unsafe_segment` identifies the highest-priority group. A segment is flagged when:

```text
speed_safety_score >= min(unsafe_threshold, top_quantile_threshold)
```

Default settings:

```text
unsafe_threshold = 70
top_quantile_unsafe = 0.90
```

This means the method captures both segments above the absolute critical threshold and the top-risk group in each country run.

## Recommended safer speed

The field `recommended_safe_speed_kmh` is created by applying:

1. a road-class base cap;
2. land-use and sensitive-place caps;
3. urban/town-context caps;
4. risk-based reductions for high score, overspeeding, exposure, and structural importance.

The recommendation is a decision-support value. It should be reviewed against local speed-limit law, road design standards, enforcement capacity, and field conditions.

## Reason codes

Each segment receives three explanation fields:

- `reason_1`;
- `reason_2`;
- `reason_3`.

Examples include:

- `land-use / town-context speed cap`;
- `dense urban road environment`;
- `urban / peri-urban road context`;
- `high overspeeding pressure`;
- `high traffic exposure`;
- `important network location`;
- `sensitive land-use / vulnerable users`;
- `data uncertainty requires review`.

Reason codes are intended to help reviewers understand why a segment was prioritised.
