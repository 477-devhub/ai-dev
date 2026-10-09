# P3 human audit queue (automatic evaluation, P2 evaluator reused)

Only flagged P3 assessments. **FULL VIDEO** = ambiguous case or final-category mismatch (P3 has no human grade). Other rows: check the decision / quoted text only. Suspected overclaims are keyword flags, not confirmed violations.

- P3 assessments flagged: 6; full video: 5; text-only: 1

| ITEM | Review | Why flagged | Model prediction | Expected observable target | Suspicious quote |
|---|---|---|---|---|---|
| ITEM_02 | **FULL VIDEO** | normalized category mismatch (final event_type); P1/P2/P3 major disagreement (raw category P1=possible_fall_or_person_down, P2=possible_scene_or_boundary_entry, P3=possible_fall_or_person_down; is_incident P1=False, P2=False, P3=True) | possible fall or person-down event · raw=possible_fall_or_person_down (0.6) · p(inc)=0.58 · conf=0.59 | possible_scene_or_boundary_entry | - |
| ITEM_03 | **FULL VIDEO** | ambiguous benchmark case; normalized category mismatch (final event_type); P1/P2/P3 major disagreement (raw category P1=possible_fall_or_person_down, P2=no_clear_incident, P3=possible_fall_or_person_down; is_incident P1=False, P2=False, P3=True) | possible fall or person-down event · raw=possible_fall_or_person_down (0.8) · p(inc)=0.7 · conf=0.75 | possible_scene_or_boundary_entry (observable only; authorization/intent not GT) | - |
| ITEM_04/CAM_02 | **FULL VIDEO** | normalized category mismatch (final event_type) | no clear incident · raw=no_clear_incident (0.87) · p(inc)=0.14 · conf=0.865 | possible_physical_conflict | - |
| ITEM_04/CAM_03 | **FULL VIDEO** | normalized category mismatch (final event_type); P1/P2/P3 major disagreement (raw category P1=no_clear_incident, P2=no_clear_incident, P3=possible_fall_or_person_down; is_incident P1=False, P2=False, P3=True) | possible fall or person-down event · raw=possible_fall_or_person_down (0.62) · p(inc)=0.51 · conf=0.565 | possible_scene_or_boundary_entry | - |
| ITEM_05 | **FULL VIDEO** | normalized category mismatch (final event_type) | possible fall or person-down event · raw=possible_fall_or_person_down (0.7) · p(inc)=0.64 · conf=0.67 | possible_physical_conflict | - |
| ITEM_07 | text check | P1/P2/P3 major disagreement (raw category P1=possible_fall_or_person_down, P2=no_clear_incident, P3=possible_physical_conflict; is_incident P1=True, P2=False, P3=True) | possible physical conflict · raw=possible_physical_conflict (0.67) · p(inc)=0.84 · conf=0.755 | possible_physical_conflict | - |
