# E2.1 영상 출처·권한·독립성 감사

조사일 2026-10-09 (Asia/Seoul). 이용 조건은 공식 Dataset/저자 페이지 기준으로 확인했다. 공개 링크 존재와 영상 이용 권한을 구분한다. 등록·승인·약관 수락이 필요한 출처는 다운로드하지 않았으며 연락/승인 신청도 대신 수행하지 않았다.

| Source / 공식 출처 | 영상·행동·수량 | 접근 / 이용 조건 | 기존 자료 중복 위험 / E2 적합성 | 실제 준비 |
|---|---|---|---|---|
| [ASSIST-IoT](https://github.com/ASSIST-IoT-SRIPAS/multimodal-fall-detection-dataset), [저자 Zenodo](https://zenodo.org/records/8340379) | Staged 연구 참고 영상; 현재 고정 commit에 사람28개, mannequin4개; 일상·자세 변화·모의 낙상·정지 자세 | 공식 repo 직접 접근, Dataset CC BY4.0 명시. 저자·출처·license 보존, 변경(clip transcoding)을 기록 | 기존 AIHub와 다른 발표 Collection이나 사람/현장/Team 관계는 Human 확인 전 미확인. 실제 CCTV domain과 Collection 다양성 제한. **Medium** | 사람28개 70,081,620bytes 수집, mannequin4개 제외, Git blob checksum/SHA256 검증 |
| [VIRAT](https://viratdata.org/) | 미국 여러 site의 실제 정상 행동·사람/차량 상호작용; Ground release 약8.5시간,11 outdoor scenes | Ground 데이터는 Protection Agreement 조건. Aerial은 별도 unrestricted release이지만 현재 E2 목적의 Ground와 구분 | 정상/CCTV domain에는 **High** 후보이나 장소/원본 Hash/촬영 관계와 사용 조건 추가 확인 필요 | 계약 승인/수락을 가정하지 않고 수집 보류 |
| [NTU RGB+D /120](https://rose1.ntu.edu.sg/dataset/actionRecognition/) | Staged Kinect; 56,880 /114,480 samples, 일상·쌍방 동작·medical proxy | 등록/요청/승인 필요, academic non-commercial. 재배포·파생 Dataset/상업 사용은 별도 허가 조건 | Hard Negative 다양성 **Medium**, CCTV viewpoint 차이. 기존 출처와 관계는 수집 후 확인 필요 | 승인 없음, 다운로드0 |
| [NTU CCTV-Fights](https://rose1.ntu.edu.sg/dataset/cctvFights/) | 1,000 videos 중 CCTV280, 기타720; conflict, 원본은 YouTube 수집 | 등록/요청/승인 및 academic-use 제한, 파생/재배포 별도 허가 | Conflict 자료 후보 **Medium**, 같은 인터넷 사건의 재업로드/기존 Team 출처 중복 위험 및 개인정보 검토 필요 | 승인 없음, 다운로드0 |
| [UP-Fall 공식 페이지](https://sites.google.com/up.edu.mx/har-up/) | Staged 일상/낙상, 공식 논문17 participants·11 activities·3 trials | 공식 공개 안내/인용 조건을 확인했으나 영상의 명확한 license 범위는 추가 확인 대상. 논문의 CC license를 영상에 그대로 적용하지 않음 | posture/Hard Negative **Medium**, 같은 site/subject grouping 필요 | 영상 권한 불확실로 다운로드0 |
| [UCF-Crime 공식 저자 페이지](https://www.crcv.ucf.edu/chenchen/datasets/), [project](https://www.crcv.ucf.edu/research/real-world-anomaly-detection-in-surveillance-videos/) | Surveillance 1,900 long videos,13 anomaly types 및 정상 자료 | 공식 다운로드 안내는 존재. 현재 확인 페이지에서 재사용/파생 영상 권한을 명확히 확정하지 못함 | 실제 CCTV **High** domain 후보, 인터넷 원본 동일 사건/재인코딩·개인정보·기존 Team overlap 확인 필수 | 약관/권리 검토 전 수집 보류 |
| [UR Fall official URL](http://fenix.univ.rzeszow.pl/~mkepski/ds/uf.html) | 이번 공식 URL 조회 실패; 영상 수/현 이용 조건 미확인 | 접근·license 미확인 | **검토 보류**, 비공식 mirror license를 원본 권한으로 간주하지 않음 | 다운로드0 |
| 팀 자체 신규 촬영 | 실제 독립 장소/세션의 보행·작업·동행/굽힘/회복. 실제 위험 촬영 강요 없이 안전한 모의 동작 | 기관/촬영장소 승인·참여자 동의·사용 범위·보존 기간 필요 | source/scene/session/participant 관리가 가능해 추가 정상/Hard Negative **High** 수집 경로 | 실제 촬영·승인은 사람이 수행, 새 영상/GT0 |

## 기존 로컬 자료

`local_inventory.json`에는 data/, downloads/, benchmark media의141개 영상 경로와5개 ZIP을 기록했다. ZIP에서 확인한 영상 member 수는20/44/54/10/0이며0은 label-only archive다. Broad inventory에서64개 경로는 기존 registry의 사용/연관 source와 직접 연결되고 나머지77개는 INDEPENDENCE_UNVERIFIED다. **77개가 새로운 독립 source라는 뜻이 아니다.** 기존 AIHub collection/take/camera 변형, reasoning/triage media 사본, mock CCTV 자료 등이 포함된다.

광범위 Raw inventory는 multi-GB 파일의 전체 Hash를 모두 새로 계산하지 않았다. Hash status를 `not computed`로 명시했고 어떤 미확인 영상도 E2에 자동 편입하지 않았다. 실제 신규28개와 Clip/Canonical은 각각 Hash를 검증한다. 기존 E2 source/group/media/이전 Canonical Hash registry는 그대로 read-only 재사용한다.

Mock CCTV는 제공 ZIP 출처·새 권한·원본 사건/물리 그룹과 Team 관계가 미확인이고 CAM02/CAM03 재사용도 명시되어 있어 신규 독립 GT로 등록하지 않았다. 기존 source manifest128, pool709, Human reviewed43(Frozen37+Challenge6), SPG01~09/scene20도 모두 exclusion reference로 보존했다.

## 자동 검사와 한계

영상 SHA256 및 source path/group 중복을 우선 검사한다. Historical 평가 MP4·mock media·등록 Scene별 raw 대표 영상과 사용 가능한 Team PNG sample의 dHash를 저장하여 재인코딩/같은 Scene 의심을 보류한다. Frame manifest에 있으나 로컬 PNG가 없는 Team sample도 발견했다. 이런 누락을 실제 source 관계를 확인한 것으로 취급하지 않는다.

dHash는 원본 시점/장면/배경 유사성의 **screening flag**다. 최대 Hamming6은 개발 전 고정된 중복 검토 기준이지 안전 판단 Threshold가 아니다. crop/mirror/다른 시간 구간·카메라 변화는 놓칠 수 있고, 단순 배경은 다른 Source에도 같게 보일 수 있다. Historical raw 전체의 모든 시간 구간을 비교한 것이 아니다. Unknown 또는 screening 미완료를 independent로 바꾸지 않는다. 일치 flag가 없어도 최종 장소/세션/배우/사건 관계의 Human evidence를 필수로 요구한다.

## 실제 신규 출처 추적

ASSIST 저자 commit `7a11c96b9a3576cef92f0795a19b3786c69a3335`에서 총28개의 사람 reference 영상을 수집했다. Git blob SHA1은 `blob <size>\0+bytes`로 검증하고 별도 SHA256를 보존했다. `sources.json`은 URL/원래 filename/license/commit의 private audit 자료다. Human Review API에는 action 이름·원본 filename·URL·모델/CV score를 반환하지 않는다. Public-facing ID는 원본 경로 Hash 순서로 배정한 opaque ID다.

Original LICENSE/README/촬영 notes를 data/에 저장했다. 이 영상은 저자 연구실험의 참고 자료이며 실제 CCTV 운영 분포가 아니다. 현재 collection 전체를1개 provisional Physical Group 및1개 unresolved Scene bucket으로 묶었다. 실제 한 Scene임을 주장하는 것이 아니라, Human 확인 없이 독립 그룹을 인위적으로 늘리지 않는 보수적 분류다. 모든 Source의 admission 상태는 INDEPENDENCE_UNVERIFIED다.

권한이 명확한 소규모 자료로 검수 환경을 먼저 준비했지만 60~100개 및 여러 독립 Physical Group 목표는 아직 달성하지 못했다. 다음 수집 우선순위는 독립 장소/세션의 실제 정상 CCTV, Hard Negative 상호작용/작업, 명확한 권한 맥락을 갖는 경계 사례, 품질/가림 사례다. Human GT 분포는 Labeling 전 알 수 없다.
