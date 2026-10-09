# 477 Organized Data Library

Original files were NOT moved or deleted.
이 Library는 원본을 보존하는 ORGANIZED VIEW + SHARE COPY입니다.

- `01_source_datasets/`: AI Hub 171 Fight/Swoon/Trespass와 AI Hub 71953 Multi-view Fight 원본의 정리된 접근 경로.
- `02_selection_artifacts/`: singleview/multiview 후보 선정 보고서, 후보 목록, contact sheets. 상위 selection 폴더 전체를 연결하지 않아 중복을 피합니다.
- `03_benchmark/benchmark_v1`: frozen `477-reasoning-v1` Benchmark 접근 경로. 읽기 전용으로 취급하며 lock이나 hash를 갱신하지 않습니다.
- `04_team_share/final_candidates_v1/`: 팀 전달용 실제 6개 unique clip과 설명·checksum.
- `04_team_share/477_final_candidates_v1.zip`: 폴더만으로 재생 가능한 독립 공유 패키지.

링크는 Windows absolute path를 사용합니다. symlink를 만들 수 없는 위치는 `.path.txt`에 실제 원본 absolute path를 기록했습니다.
`.path.txt`를 열고 해당 경로를 파일 탐색기에서 여세요. 원본 경로는 `D:/projects/477`이며 WSL에서는 `/mnt/d/projects/477`에 해당합니다.
Library의 view는 이 프로젝트에 의존하지만 공유 ZIP은 원본 경로에 의존하지 않습니다.

Swoon/Trespass의 `extracted/`는 active extracted dataset입니다.
`archive_recovery_artifacts/`의 ZIP 및 `.zip.part*`는 manifest category `archive_recovery_artifact`이며,
복구/다운로드 산출물로서 active extracted dataset과 구분합니다. 원본 recovery 파일도 보존했습니다.

AI Hub 71953은 한 JSON이 한 사건의 c1/c2 영상을 함께 연결하는 구조입니다.
```
One event
 ├── CAM A / c1
 └── CAM B / c2
```
공식 frame-level synchronization은 제공되지 않았습니다.

**TEAM SHARE ≠ MODEL INPUT**. 팀 공유용 descriptive filename으로 모델 입력을 구성하지 마세요.
P0~P4는 계속 `benchmark_v1/public_manifest.json`, `benchmark_v1/model_input/`,
`benchmark_v1/scripts/load_model_input.py`를 사용합니다.

`DATA_MANIFEST.csv/json`의 size_bytes는 참조 대상의 논리적 크기이며 중첩 view가 있으므로 합산하지 마세요.
실제 저장 파일 byte 수는 `storage_report.md`를 참고하세요. symlink target 크기는 물리 크기에 포함하지 않습니다.
원본 파일 작업 전 상태는 `original_state_before.json`, 안전 검증 결과는 `verification_report.json`에 기록합니다.

## 2026-10-07 Cleanup
temporary extraction removed after benchmark freeze.
검증된 `.zip.part*`, 복구 intermediate TAR, selection tmp와 Python cache를 제거했습니다.
삭제된 recovery part를 가리키던 링크만 제거하고 DATA_MANIFEST에서 해당 view 항목을 제외했습니다.
completed ZIP, extracted dataset, downloads, 보고서/contact sheets, frozen Benchmark와 팀 공유 패키지는 보존했습니다.
상단의 원본 보존 설명과 `original_state_before.json`/`verification_report.json`은 Library 생성 시점 기록입니다.
후속 cleanup의 실제 삭제 목록과 현재 검증 결과는 `CLEANUP_MANIFEST.json`/`CLEANUP_REPORT.md`를 참고하세요.
