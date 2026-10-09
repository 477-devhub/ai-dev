from build_inventory import *
from PIL import Image
import zlib
def main():
 inv=read('inventory_details.json');cs=read('candidates.json');rank=read('ranking_combinations.json');errs=[]
 with (ROOT/'candidates.csv').open(encoding='utf-8-sig',newline='') as f:csvrows=list(csv.DictReader(f))
 if [(r['candidate_id'],r['scenario'],r['video_path']) for r in csvrows]!=[(r['candidate_id'],r['scenario'],r['video_path']) for r in cs]:errs.append('CSV/JSON mismatch')
 if len(read('source_annotation_facts.json'))!=len(inv):errs.append('Source facts count mismatch')
 for r in inv:
  if r['zip_path']:
   with zipfile.ZipFile(r['zip_path']) as z:raw=z.read(r['annotation_path'].split('::',1)[1]);actual=z.getinfo(r['zip_member']).file_size
  else:raw=Path(r['annotation_path']).read_bytes();actual=Path(r['video_path']).stat().st_size
  if hashlib.sha256(raw).hexdigest()!=r['annotation_sha256']:errs.append('Original annotation changed: '+r['filename'])
  if actual!=r['file_size']:errs.append('Source size changed: '+r['filename'])
 for c in cs:
  if not Path(c['local_video_path']).exists():errs.append('Missing candidate video '+c['candidate_id'])
  for k in ['contact_sheet_path','temporal_sheet_path']:
   try:
    with Image.open(c[k]) as im:im.verify()
   except Exception as e:errs.append(str(e))
  for k in ['sampled_frames','temporal_sampled_frames']:
   t=[f['decoded_seconds'] for f in c[k]]
   if t!=sorted(t):errs.append('Nonchronological sheet '+c['candidate_id'])
  if not all(1<=c[k]<=5 and c['score_reasons'][k] for k in ['event_visibility','event_clarity','temporal_value','visual_quality','reasoning_value','demo_suitability','ambiguity']):errs.append('Invalid scores '+c['candidate_id'])
  if c['source_candidate_id'] in read('review_decisions.json')['excluded']:errs.append('Excluded video selected')
 for r in rank:
  for cam,v in r['cameras'].items():
   if not (0<=v['suggested_playback_start']<v['suggested_playback_end']<=v['duration']):errs.append('Bad ranking seek interval')
 # Verify selective extracted videos against source ZIP CRC, streamed with no copies.
 zpath=next((DATA/'downloads/fight').rglob('insidedoor_04.zip'))
 with zipfile.ZipFile(zpath) as z:
  for item in read('temporary_files.json'):
   p=Path(item['path']);crc=0
   with p.open('rb') as f:
    while chunk:=f.read(1024*1024):crc=zlib.crc32(chunk,crc)
   member=p.relative_to(ROOT/'tmp/fight').as_posix()
   if crc!=z.getinfo(member).CRC:errs.append('Extracted CRC mismatch '+member)
 dump('validation_result.json',{'passed':not errs,'errors':errs,'inventory_rows':len(inv),'candidate_rows':len(cs),'ranking_combinations':len(rank),'source_annotation_hashes_checked':len(inv),'temporary_zip_crc_checked':len(read('temporary_files.json')),'checks':'CSV/JSON candidate rows, image decoding, chronological frame timestamps, scores/reasons, source XML hashes and sizes, extracted CRC, ranking playback bounds'})
 total=sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file() and p.name!='storage_summary.json');extract=sum(x['size'] for x in read('temporary_files.json'))
 dump('storage_summary.json',{'evaluation_selection_bytes_excluding_this_small_summary':total,'fight_extracted_bytes':extract,'fight_extracted_video_bytes':sum(x['size'] for x in read('temporary_files.json') if x['path'].endswith('.mp4')),'contact_sheets_bytes':sum(p.stat().st_size for p in (ROOT/'contact_sheets').glob('*.jpg')),'free_disk_bytes_after':shutil.disk_usage(ROOT).free})
 print('Validation:', 'PASS' if not errs else 'FAIL', 'errors:',len(errs),'total GiB:',round(total/1024**3,4),'Fight extracted GiB:',round(extract/1024**3,4))
 if errs:raise SystemExit(1)
if __name__=='__main__':main()
