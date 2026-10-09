# 477 Cleanup Report

Cleanup date: 2026-10-07T16:44:56+09:00 (Asia/Seoul)

Before total project size: 00000000173661714665 bytes
After total project size: 00000000096240096322 bytes
Freed bytes (net): 00000000077421618343
Freed GiB (net): 000072.104501
Deleted file content bytes (gross): 77421620536
Deleted content GiB (gross): 72.104503

Sizes count regular-file contents and exclude symlink targets, allocation slack and transient cleanup tooling.
Net reduction includes updated/new cleanup reports; gross is the pre-deletion sum.

## Before / After

| Location | Before bytes | After bytes |
|---|---:|---:|
| project | 00000000173661714665 | 00000000096240096322 |
| data | 00000000148839677500 | 00000000074420353355 |
| downloads | 00000000020992863074 | 00000000020992863074 |
| evaluation_selection | 00000000003049760874 | 00000000000047464483 |
| benchmark_v1 | 00000000000429551490 | 00000000000429551490 |
| organized_data | 00000000000349840808 | 00000000000349843001 |

## Removed

| Category | Entries | Bytes measured before removal | GiB |
|---|---:|---:|---:|
| zip_part | 36 | 37209651953 | 34.654189 |
| tar_intermediate | 1 | 37209672192 | 34.654208 |
| single_view_tmp | 1 | 2259157209 | 2.104004 |
| multi_view_tmp | 1 | 743055292 | 0.692024 |
| python_cache | 2 | 83890 | 0.000078 |
| empty_directory | 1 | 0 | 0.000000 |
| removed_recovery_symlink | 36 | 0 | 0.000000 |

## Pre-deletion evidence

- Benchmark validation: PASS before deletion.
- Team share: 6 regular MP4 files; checksums verified; ZIP SHA256 matches supplied frozen hash.
- Broken organized_data links before cleanup: 0.
- Swoon extracted: 20 MP4 / 20 XML; Trespass extracted: 44 MP4 / 44 XML.
- Both tmp directories contained only MP4/XML, with no reports or links.
- TAR member listing: 36 regular zip-part members; no other unique files.
- All TAR members were streamed without extraction and compared byte-for-byte against recovered parts and retained completed ZIP ranges. Ranges covered both completed ZIPs fully.
- Complete archives retained:
  - `D:/projects/477/data/recovered/19.이상행동CCTV/05.실신(swoon)/실외/outsidedoor_11.zip` — 10968921745 bytes
  - `D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip` — 26240730208 bytes

### TAR member dry run

| Member | Size bytes | Byte match |
|---|---:|---|
| 19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part0 | 1073741824 | True |
| 19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part1073741824 | 1073741824 | True |
| 19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part2147483648 | 1073741824 | True |
| 19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part3221225472 | 1073741824 | True |
| 19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part4294967296 | 1073741824 | True |
| 19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part5368709120 | 1073741824 | True |
| 19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part6442450944 | 1073741824 | True |
| 19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part7516192768 | 1073741824 | True |
| 19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part8589934592 | 1073741824 | True |
| 19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part9663676416 | 1073741824 | True |
| 19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part10737418240 | 1073741824 | True |
| 19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part11811160064 | 1073741824 | True |
| 19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part12884901888 | 1073741824 | True |
| 19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part13958643712 | 1073741824 | True |
| 19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part15032385536 | 1073741824 | True |
| 19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part16106127360 | 1073741824 | True |
| 19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part17179869184 | 1073741824 | True |
| 19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part18253611008 | 1073741824 | True |
| 19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part19327352832 | 1073741824 | True |
| 19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part20401094656 | 1073741824 | True |
| 19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part21474836480 | 1073741824 | True |
| 19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part22548578304 | 1073741824 | True |
| 19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part23622320128 | 1073741824 | True |
| 19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part24696061952 | 1073741824 | True |
| 19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part25769803776 | 470926432 | True |
| 19.이상행동CCTV/05.실신(swoon)/실외/outsidedoor_11.zip.part0 | 1073741824 | True |
| 19.이상행동CCTV/05.실신(swoon)/실외/outsidedoor_11.zip.part1073741824 | 1073741824 | True |
| 19.이상행동CCTV/05.실신(swoon)/실외/outsidedoor_11.zip.part2147483648 | 1073741824 | True |
| 19.이상행동CCTV/05.실신(swoon)/실외/outsidedoor_11.zip.part3221225472 | 1073741824 | True |
| 19.이상행동CCTV/05.실신(swoon)/실외/outsidedoor_11.zip.part4294967296 | 1073741824 | True |
| 19.이상행동CCTV/05.실신(swoon)/실외/outsidedoor_11.zip.part5368709120 | 1073741824 | True |
| 19.이상행동CCTV/05.실신(swoon)/실외/outsidedoor_11.zip.part6442450944 | 1073741824 | True |
| 19.이상행동CCTV/05.실신(swoon)/실외/outsidedoor_11.zip.part7516192768 | 1073741824 | True |
| 19.이상행동CCTV/05.실신(swoon)/실외/outsidedoor_11.zip.part8589934592 | 1073741824 | True |
| 19.이상행동CCTV/05.실신(swoon)/실외/outsidedoor_11.zip.part9663676416 | 1073741824 | True |
| 19.이상행동CCTV/05.실신(swoon)/실외/outsidedoor_11.zip.part10737418240 | 231503505 | True |

### Zip part dry run

| File | Size bytes |
|---|---:|
| D:/projects/477/data/recovered/19.이상행동CCTV/05.실신(swoon)/실외/outsidedoor_11.zip.part0 | 1073741824 |
| D:/projects/477/data/recovered/19.이상행동CCTV/05.실신(swoon)/실외/outsidedoor_11.zip.part1073741824 | 1073741824 |
| D:/projects/477/data/recovered/19.이상행동CCTV/05.실신(swoon)/실외/outsidedoor_11.zip.part10737418240 | 231503505 |
| D:/projects/477/data/recovered/19.이상행동CCTV/05.실신(swoon)/실외/outsidedoor_11.zip.part2147483648 | 1073741824 |
| D:/projects/477/data/recovered/19.이상행동CCTV/05.실신(swoon)/실외/outsidedoor_11.zip.part3221225472 | 1073741824 |
| D:/projects/477/data/recovered/19.이상행동CCTV/05.실신(swoon)/실외/outsidedoor_11.zip.part4294967296 | 1073741824 |
| D:/projects/477/data/recovered/19.이상행동CCTV/05.실신(swoon)/실외/outsidedoor_11.zip.part5368709120 | 1073741824 |
| D:/projects/477/data/recovered/19.이상행동CCTV/05.실신(swoon)/실외/outsidedoor_11.zip.part6442450944 | 1073741824 |
| D:/projects/477/data/recovered/19.이상행동CCTV/05.실신(swoon)/실외/outsidedoor_11.zip.part7516192768 | 1073741824 |
| D:/projects/477/data/recovered/19.이상행동CCTV/05.실신(swoon)/실외/outsidedoor_11.zip.part8589934592 | 1073741824 |
| D:/projects/477/data/recovered/19.이상행동CCTV/05.실신(swoon)/실외/outsidedoor_11.zip.part9663676416 | 1073741824 |
| D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part0 | 1073741824 |
| D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part1073741824 | 1073741824 |
| D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part10737418240 | 1073741824 |
| D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part11811160064 | 1073741824 |
| D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part12884901888 | 1073741824 |
| D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part13958643712 | 1073741824 |
| D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part15032385536 | 1073741824 |
| D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part16106127360 | 1073741824 |
| D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part17179869184 | 1073741824 |
| D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part18253611008 | 1073741824 |
| D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part19327352832 | 1073741824 |
| D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part20401094656 | 1073741824 |
| D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part2147483648 | 1073741824 |
| D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part21474836480 | 1073741824 |
| D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part22548578304 | 1073741824 |
| D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part23622320128 | 1073741824 |
| D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part24696061952 | 1073741824 |
| D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part25769803776 | 470926432 |
| D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part3221225472 | 1073741824 |
| D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part4294967296 | 1073741824 |
| D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part5368709120 | 1073741824 |
| D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part6442450944 | 1073741824 |
| D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part7516192768 | 1073741824 |
| D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part8589934592 | 1073741824 |
| D:/projects/477/data/recovered/19.이상행동CCTV/07.침입(trespass)/실외/outsidedoor_01.zip.part9663676416 | 1073741824 |

## Preserved and final validation

- benchmark_v1: PASS; all benchmark file sizes/mtime/SHA256 unchanged; modified files = 0.
- Downloads, completed ZIPs, Swoon/Trespass extracted, candidate reports, scripts, contact sheets and experiment plan: preserved.
- Every retained original regular file compared against pre-cleanup size/mtime; protected Benchmark and team-share contents additionally hash-checked.
- Team share regular MP4: 6; share ZIP SHA256: MATCH.
- Share ZIP SHA256: `1e535afa6ee8dad73709cf258693217c9172135411f7d4fbc94247ebb645ff11`
- Broken organized_data links after cleanup: 0.
- Only deleted part links and related Library records updated under explicit user authorization.
- Original Library creation snapshots kept as historical records.
- download.log and download.pid retained: process namespace could not be reliably established, and both are small.
- No additional second-stage deletion performed. Downloads, completed ZIPs and extracted datasets remain outside cleanup scope.
