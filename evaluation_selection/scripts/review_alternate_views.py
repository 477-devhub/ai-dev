from extract_contact_sheets import *
import sys
def main():
 rows=read('inventory_details.json');chosen=read('alternate_views.json') if (ROOT/'alternate_views.json').exists() and '--refresh' not in sys.argv else []
 specs=[('S08','710-2','spring'),('S09','710-3','spring'),('S10','710-4','spring'),('S11','710-5','spring'),('S12','710-6','spring'),('S13','710-2','summer'),('S14','710-4','summer'),('S15','710-5','summer'),('S16','710-6','summer')]
 for cid,ident,season in specs:
  if any(r['candidate_id']==cid for r in chosen):continue
  cam='cam01' if cid in ['S14','S15','S16'] else 'cam02'
  r=next(r for r in rows if r['filename'].startswith(ident+'_'+cam+'_') and r['filename'].endswith('_'+season+'.mp4')).copy();r.update(candidate_id=cid,scenario='B',contact_sheet_path=str(ROOT/'contact_sheets'/f'{cid}.jpg'),temporal_sheet_path=str(ROOT/'contact_sheets'/f'{cid}_temporal.jpg'))
  a,b=r['event_start'],r['event_end'];r['sampled_frames']=sheet(r,[a-8,a-2,a,a+(b-a)*.2,a+(b-a)*.4,a+(b-a)*.6,a+(b-a)*.8,b,b+10],r['contact_sheet_path']);r['temporal_sampled_frames']=sheet(r,[a-8+i*(b-a+20)/23 for i in range(24)],r['temporal_sheet_path'],cols=4,w=400);chosen.append(r);print(cid,'alternate view ready',flush=True)
 dump('alternate_views.json',chosen)
if __name__=='__main__':main()
