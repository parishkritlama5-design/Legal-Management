# Screenshot Placeholder — Operational Bottleneck Dashboard

**File to capture:** `operational_bottleneck.png`
**Audience:** Director of Operations, Case Manager Supervisors

## What this screenshot should show
Where matters pile up and stall, so operations can intervene.

**Visuals:**
- **Bar**: open cases & avg days-in-stage by stage (the records stages are the
  known choke point).
- **Bucketed bar**: stalled cases by inactivity bucket (31–60 / 61–90 / 90+ days).
- **Aging table**: outstanding medical records by status with avg days
  outstanding.
- **Worklist table**: top inactive open cases (>30 days no activity) with manager
  and days inactive, for direct triage.

**Slicers:** stage, case manager, case type, inactivity bucket.

## Capture checklist
- [ ] Bottleneck stage(s) visually obvious
- [ ] Stalled-case worklist is actionable (case_id, manager, days inactive)
- [ ] Records-aging quantified in days
- [ ] At-risk caseload (from the model) optionally overlaid for prioritization
