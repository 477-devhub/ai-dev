"""Post-freeze wrapper around unchanged validator logic (avoids legacy CLI detail-format bug)."""
import sys
from common import BENCH, RUN, read, digest, write, now

def main():
    lock=read(BENCH/'BENCHMARK_LOCK.json')
    drift=[p for p,h in lock['sha256'].items() if not (BENCH/p).is_file() or digest(BENCH/p)!=h]
    if drift:
        raise RuntimeError(f'Benchmark lock drift: {drift}')
    sys.path.insert(0,str(BENCH/'scripts'))
    from _priority_gt import validate_built
    result=validate_built()
    if not result['all_pass']:
        raise RuntimeError('Frozen benchmark validation failed')
    write(RUN/'benchmark_freeze_verification.json',{'verified_at':now(),'all_pass':True,
        'locked_files':len(lock['sha256']),'benchmark_lock_sha256':digest(BENCH/'BENCHMARK_LOCK.json'),
        'note':'Underlying frozen validator checks all pass. Original CLI has a list-detail formatting bug after freeze; this wrapper does not change any frozen byte.'})
    print(f"FROZEN BENCHMARK VALIDATION PASS: {len(lock['sha256'])} locked files, all GT/media/separation checks passed")

if __name__=='__main__':
    main()
