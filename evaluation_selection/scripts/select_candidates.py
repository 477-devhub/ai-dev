from build_inventory import *
# Frozen annotation-informed review shortlist; no visual scores inferred from filenames.
SPECS=[('F01','435-2','cam01','spring'),('F02','435-3','cam02','summer'),('F03','435-4','cam03','winter'),('F04','435-5','cam01','spring'),('F05','435-6','cam02','winter'),('F06','439-1','cam01','spring'),('S01','710-2','cam01','spring'),('S02','710-3','cam01','spring'),('S03','710-4','cam01','spring'),('S04','710-5','cam01','spring'),('S05','710-6','cam01','spring'),('S06','710-2','cam01','summer'),('S07','710-3','cam01','summer'),('T01','146-1','cam01','spring'),('T02','146-2','cam01','spring'),('T03','146-3','cam01','spring'),('T04','146-4','cam01','spring'),('T05','146-5','cam01','spring'),('T06','145-3','cam01','summer'),('T07','145-1','cam02','spring'),('T08','145-4','cam01','spring')]
def main():
 rows=read('inventory_details.json');chosen=[]
 for cid,ident,cam,season in SPECS:
  r=next(r for r in rows if r['filename'].startswith(ident+'_') and '_'+cam+'_' in r['filename'] and r['filename'].endswith('_'+season+'.mp4'))
  chosen.append({**r,'candidate_id':cid,'scenario':{'F':'A','S':'B','T':'C'}[cid[0]],'contact_sheet_path':str(ROOT/'contact_sheets'/f'{cid}.jpg'),'temporal_sheet_path':str(ROOT/'contact_sheets'/f'{cid}_temporal.jpg')})
 dump('review_shortlist.json',chosen)
 print('Annotation shortlist:',len(chosen),'Fight bytes requiring extraction:',sum(r['file_size'] for r in chosen if r['zip_path']))
if __name__=='__main__': main()
