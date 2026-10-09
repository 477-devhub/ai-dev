# Human audit queue (automatic evaluation v1)

Only flagged assessments are listed. **FULL VIDEO** = the clip must be re-watched (no existing human grade and the case is ambiguous or the category mismatches). Other rows need only the quoted text / decision checked. Suspected overclaims are keyword flags, not confirmed violations. P0/P1 rows already have reviewer_01 grades; they are listed for completeness.

- assessments flagged: 25; requiring full video review: 4

| ITEM | Pipeline | Review | Why flagged | Model prediction | Expected observable target | Suspicious quote |
|---|---|---|---|---|---|---|
| ITEM_03 | P2 | **FULL VIDEO** | ambiguous benchmark case; normalized category mismatch; P1/P2 large disagreement (category or is_incident differs) | no clear incident · is_incident=False · conf=0.5242 | possible_scene_or_boundary_entry (observable only; authorization/intent not GT) | - |
| ITEM_04/CAM_03 | P2 | **FULL VIDEO** | normalized category mismatch | no clear incident · is_incident=False · conf=0.454 | possible_scene_or_boundary_entry | - |
| ITEM_05 | P2 | **FULL VIDEO** | normalized category mismatch; very low confidence (0.38); P1/P2 large disagreement (category or is_incident differs) | no clear incident · is_incident=False · conf=0.38 | possible_physical_conflict | - |
| ITEM_07 | P2 | **FULL VIDEO** | normalized category mismatch; very low confidence (0.3917); P1/P2 large disagreement (category or is_incident differs) | no clear incident · is_incident=False · conf=0.3917 | possible_physical_conflict | - |
| ITEM_01 | P2 | text check | internal contradiction: is_incident=false but event_type='possible fall or person-down event'; P1/P2 large disagreement (category or is_incident differs) | possible fall or person-down event · is_incident=False · conf=0.6587 | possible_fall_or_person_down | - |
| ITEM_02 | P2 | text check | P1/P2 large disagreement (category or is_incident differs) | possible scene or boundary entry (boundary semantics unknown) · is_incident=False · conf=0.584 | possible_scene_or_boundary_entry | - |
| ITEM_04/CAM_01 | P2 | text check | internal contradiction: is_incident=false but event_type='possible fall or person-down event'; P1/P2 large disagreement (category or is_incident differs) | possible fall or person-down event · is_incident=False · conf=0.6964 | possible_fall_or_person_down | - |
| ITEM_04/CAM_02 | P2 | text check | internal contradiction: is_incident=false but event_type='possible physical conflict'; P1/P2 large disagreement (category or is_incident differs) | possible physical conflict · is_incident=False · conf=0.4455 | possible_physical_conflict | - |
| ITEM_06 | P2 | text check | internal contradiction: is_incident=false but event_type='possible physical conflict'; very low confidence (0.3727); P1/P2 large disagreement (category or is_incident differs) | possible physical conflict · is_incident=False · conf=0.3727 | possible_physical_conflict | - |
| ITEM_01 | P1 | graded | P1/P2 large disagreement (category or is_incident differs) | possible fall or person-down event · is_incident=True · conf=0.925 | possible_fall_or_person_down | - |
| ITEM_02 | P1 | graded | normalized category mismatch; internal contradiction: is_incident=false but event_type='possible fall or person-down event'; P1/P2 large disagreement (category or is_incident differs) | possible fall or person-down event · is_incident=False · conf=0.685 | possible_scene_or_boundary_entry | - |
| ITEM_03 | P1 | graded | ambiguous benchmark case; normalized category mismatch; internal contradiction: is_incident=false but event_type='possible fall or person-down event'; P1/P2 large disagreement (category or is_incident differs) | possible fall or person-down event · is_incident=False · conf=0.705 | possible_scene_or_boundary_entry (observable only; authorization/intent not GT) | - |
| ITEM_04/CAM_01 | P1 | graded | P1/P2 large disagreement (category or is_incident differs) | possible fall or person-down event · is_incident=True · conf=0.96 | possible_fall_or_person_down | - |
| ITEM_04/CAM_02 | P1 | graded | normalized category mismatch; P1/P2 large disagreement (category or is_incident differs) | no clear incident · is_incident=False · conf=0.65 | possible_physical_conflict | - |
| ITEM_04/CAM_03 | P1 | graded | normalized category mismatch | no clear incident · is_incident=False · conf=0.44 | possible_scene_or_boundary_entry | - |
| ITEM_05 | P1 | graded | normalized category mismatch; P1/P2 large disagreement (category or is_incident differs) | possible fall or person-down event · is_incident=True · conf=0.44 | possible_physical_conflict | - |
| ITEM_06 | P1 | graded | normalized category mismatch; P1/P2 large disagreement (category or is_incident differs) | possible fall or person-down event · is_incident=True · conf=0.625 | possible_physical_conflict | - |
| ITEM_07 | P1 | graded | normalized category mismatch; P1/P2 large disagreement (category or is_incident differs) | possible fall or person-down event · is_incident=True · conf=0.805 | possible_physical_conflict | - |
| ITEM_01 | P0 | graded | internal contradiction: is_incident=false but event_type='low or horizontal posture observed (onset not observed)' | low or horizontal posture observed (onset not observed) · is_incident=False · conf=0.744 | possible_fall_or_person_down | - |
| ITEM_03 | P0 | graded | ambiguous benchmark case | person movement / scene entry observed · is_incident=False · conf=0.782 | possible_scene_or_boundary_entry (observable only; authorization/intent not GT) | - |
| ITEM_04/CAM_01 | P0 | graded | internal contradiction: is_incident=false but event_type='low or horizontal posture observed (onset not observed)' | low or horizontal posture observed (onset not observed) · is_incident=False · conf=0.738 | possible_fall_or_person_down | - |
| ITEM_04/CAM_02 | P0 | graded | normalized category mismatch | no incident-like pattern detected · is_incident=False · conf=0.51 | possible_physical_conflict | - |
| ITEM_05 | P0 | graded | normalized category mismatch | person movement / scene entry observed · is_incident=False · conf=0.627 | possible_physical_conflict | - |
| ITEM_06 | P0 | graded | normalized category mismatch | person movement / scene entry observed · is_incident=False · conf=0.806 | possible_physical_conflict | - |
| ITEM_07 | P0 | graded | normalized category mismatch | person movement / scene entry observed · is_incident=False · conf=0.779 | possible_physical_conflict | - |
