from build_multiview_inventory import *
def main():
 pairs=read('multiview_inventory.json');short=[]
 for p in pairs:
  if not p['valid_pair']:continue
  p['annotation_reason_for_candidate']='Source JSON co-lists two views and supplies different view-specific stage descriptions/evidence; all five local incidents reviewed because fewer than requested 15–20 are available.'
  p['number_of_people_annotation']={c:v['number_of_annotated_people'] for c,v in p['cameras'].items()}
  p['source_actions_private']={c:v['camera_description_private'] for c,v in p['cameras'].items()}
  short.append(p)
 dump('annotation_shortlist_private.json',short)
 print('Annotation-first shortlist:',len(short),'pairs;',sum(v['file_size'] for p in short for v in p['cameras'].values()),'planned video bytes')
if __name__=='__main__':main()
