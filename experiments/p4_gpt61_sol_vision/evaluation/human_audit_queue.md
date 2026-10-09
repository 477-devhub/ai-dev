# P4 human audit queue (automatic evaluation; P2 evaluator reused unchanged)

Only flagged P4 assessments. **FULL VIDEO** = ambiguous case or final-category mismatch. Other rows: check decision / quoted text. Suspected overclaims are keyword flags (negated sentences skipped), not confirmed violations.

- P4 assessments flagged: 5; full video: 1; text-only: 4

| ITEM | Review | Why flagged | Model prediction | Expected observable target | Suspicious quote |
|---|---|---|---|---|---|
| ITEM_03 | **FULL VIDEO** | ambiguous benchmark case; P3/P4 disagreement (raw P3=possible_fall_or_person_down inc=True; P4=possible_scene_or_boundary_entry inc=True) | possible scene or boundary entry (boundary semantics unknown) · raw=possible_scene_or_boundary_entry (0.97) · p(inc)=0.84 · conf=0.905 | possible_scene_or_boundary_entry (observable only; authorization/intent not GT) | - |
| ITEM_02 | text check | P3/P4 disagreement (raw P3=possible_fall_or_person_down inc=True; P4=possible_scene_or_boundary_entry inc=True) | possible scene or boundary entry (boundary semantics unknown) · raw=possible_scene_or_boundary_entry (0.99) · p(inc)=0.98 · conf=0.985 | possible_scene_or_boundary_entry | - |
| ITEM_04/CAM_02 | text check | P3/P4 disagreement (raw P3=no_clear_incident inc=False; P4=possible_physical_conflict inc=True) | possible physical conflict · raw=possible_physical_conflict (0.82) · p(inc)=0.85 · conf=0.835 | possible_physical_conflict | - |
| ITEM_04/CAM_03 | text check | P3/P4 disagreement (raw P3=possible_fall_or_person_down inc=True; P4=possible_scene_or_boundary_entry inc=True) | possible scene or boundary entry (boundary semantics unknown) · raw=possible_scene_or_boundary_entry (0.99) · p(inc)=0.98 · conf=0.985 | possible_scene_or_boundary_entry | - |
| ITEM_05 | text check | P3/P4 disagreement (raw P3=possible_fall_or_person_down inc=True; P4=possible_physical_conflict inc=True) | possible physical conflict · raw=possible_physical_conflict (0.9) · p(inc)=0.94 · conf=0.92 | possible_physical_conflict | - |
