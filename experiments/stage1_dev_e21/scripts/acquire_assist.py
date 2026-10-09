"""Limited download from pinned author repository; license + Git blob integrity retained."""
import sys
import urllib.request
import hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from dev_common import ROOT,read,write,sha,now


def main():
    tree=read(ROOT/'data/assist_tree.json'); commit=tree['sha']
    entries=[x for x in tree['tree'] if x['path'].startswith('videos/') and x['path'].endswith('.mp4') and 'mannequin_videos' not in x['path']]
    total=sum(x['size'] for x in entries)
    if total>90_000_000 or len(entries)>32: raise ValueError('limited download budget exceeded')
    if not (ROOT/'data/ASSIST_LICENSE').is_file(): raise ValueError('license evidence missing')
    sources=[]
    # Opaque shuffled review order, unrelated to action category or original filename.
    entries.sort(key=lambda x:hashlib.sha256(x['path'].encode()).hexdigest())
    for n,e in enumerate(entries,1):
        sid=f'DEVSRC_{n:03d}'; p=ROOT/'media/sources'/f'{sid}.mp4'
        url=f"https://raw.githubusercontent.com/ASSIST-IoT-SRIPAS/multimodal-fall-detection-dataset/{commit}/{e['path']}"
        if not p.exists():
            p.parent.mkdir(parents=True,exist_ok=True)
            with urllib.request.urlopen(url,timeout=60) as response: b=response.read(e['size']+1)
            if len(b)!=e['size'] or hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()!=e['sha']:
                raise ValueError('Git blob checksum/size mismatch')
            p.write_bytes(b)
        elif p.stat().st_size!=e['size'] or hashlib.sha1(f'blob {e["size"]}\0'.encode()+p.read_bytes()).hexdigest()!=e['sha']:
            raise ValueError('existing source altered')
        sources.append({'source_id':sid,'dataset':'ASSIST-IoT multimodal fall detection',
            'source_video_path':str(p.resolve()),'source_video_sha256':sha(p),'source_url':url,
            'upstream_path_private':e['path'],'upstream_blob_sha1':e['sha'],'upstream_commit':commit,
            'license':'CC-BY-4.0','license_evidence':str(ROOT/'data/ASSIST_LICENSE'),
            'scene_group_id':'DEVSCENE_ASSIST_UNRESOLVED','physical_group_id':'DEVPHYS_ASSIST_COLLECTION',
            'camera_id':'CAM_01','independence_status':'INDEPENDENCE_UNVERIFIED',
            'capture_context_neutral':'Research staging. Site rules and authorization context are not supplied.',
            'captured_at':None,'acquired_at':now()})
    write(ROOT/'data/sources.json',{'schema_version':'e21-sources-v1','sources':sources,
        'attribution':'ASSIST-IoT-SRIPAS: Danilenka, Sowiński, Kobus, Dąbrowska, Rachwał, Bogacka, Baszczyński; CC BY 4.0; https://github.com/ASSIST-IoT-SRIPAS/multimodal-fall-detection-dataset; downloaded unchanged.',
        'total_download_bytes':total,'selection':'All 28 human reference videos at pinned commit; four mannequin files excluded using author directory metadata; no Human GT inferred.'})
    print('sources',len(sources),'bytes',total)


if __name__=='__main__': main()
