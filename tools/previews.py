#!/usr/bin/env python3
"""Named link previews for shared pages (Firebase Spark, static hosting only).

Link-preview crawlers never see the #p=<id> part of a page link and do not run JS, so every page
previews as the site title. This script publishes a tiny static stub per chosen page at
/s/<slug>/ that carries only the page TITLE as og:title and then redirects to the real page link.
The stub holds no page content and does not change who can open the page (the redirect target still
enforces its normal access rules).

Usage (env: SHARED_PAGES_PROJECT, SHARED_PAGES_REFRESH_TOKEN_FILE; optional SHARED_PAGES_CLIENT_ID/SECRET):
  previews.py share PAGE_ID [--title "preview title"]   publish/refresh the stub, print the share link
  previews.py rename PAGE_ID "new title"                 change page title (app + preview) and refresh stub if one exists
  previews.py put /path LOCAL_FILE                       replace/add ONE hosting file, full manifest kept
  previews.py list                                       show which pages have a stub
Never clobbers: the new hosting version is the FULL current manifest (all live hashes) plus the stub
files; it aborts if the live release moved while preparing. The previous release stays as rollback.
"""
import sys,os,json,gzip,hashlib,urllib.request,urllib.parse,html,re
P=os.environ.get('SHARED_PAGES_PROJECT') or sys.exit('Set SHARED_PAGES_PROJECT to your Firebase project id')
CID=os.environ.get('SHARED_PAGES_CLIENT_ID','563584335869-fgrhgmd47bqnekij5i8b5pr03ho849e6.apps.googleusercontent.com')  # public firebase-tools OAuth client
CSEC=os.environ.get('SHARED_PAGES_CLIENT_SECRET','j9iVZfS8kkCEFUPaAeJV0sAi')
HOST=f'https://{P}.web.app'
API='https://firebasehosting.googleapis.com/v1beta1'
def req(url,data=None,method=None,headers=None,raw=False):
    h={'Authorization':'Bearer '+TOKEN}; h.update(headers or {})
    if data is not None and not raw: data=json.dumps(data).encode(); h['Content-Type']='application/json'
    r=urllib.request.Request(url,data,h,method=method)
    try: b=urllib.request.urlopen(r).read()
    except urllib.error.HTTPError as e: raise SystemExit(f'HTTP {e.code} {url}: {e.read()[:300]!r}')
    return json.loads(b) if b and not raw else b
def token():
    rt=open(os.environ['SHARED_PAGES_REFRESH_TOKEN_FILE']).read().strip()
    d=urllib.parse.urlencode({'grant_type':'refresh_token','refresh_token':rt,'client_id':CID,'client_secret':CSEC}).encode()
    return json.load(urllib.request.urlopen('https://oauth2.googleapis.com/token',d))['access_token']
TOKEN=token()
def db():
    return json.loads(urllib.request.urlopen(HOST+'/__/firebase/init.json').read())['databaseURL']
def rtdb(path,data=None,method='GET'):
    u=f'{db()}/{path}.json?access_token={TOKEN}'
    r=urllib.request.Request(u,None if data is None else json.dumps(data).encode(),method=method)
    return json.loads(urllib.request.urlopen(r).read())
def slug(pid): return hashlib.sha256(('preview:'+pid).encode()).hexdigest()[:20]
def stub(pid,title):
    t=html.escape(title,quote=True); link=f'{HOST}/#p={pid}'; s=f'{HOST}/s/{slug(pid)}/'
    return f'''<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{t}</title><meta property="og:type" content="website"><meta property="og:title" content="{t}"><meta property="og:description" content="דף משותף - נדרשת כניסה לפי ההרשאות של הדף"><meta property="og:url" content="{s}"><meta property="og:image" content="{HOST}/og.jpg"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta name="twitter:card" content="summary_large_image"><meta name="robots" content="noindex"><meta http-equiv="refresh" content="0;url={link}"><script>location.replace({json.dumps(link)})</script></head><body><p><a href="{link}">{t}</a></p></body></html>'''
def live():
    rel=req(f'{API}/sites/{P}/releases?pageSize=1')['releases'][0]
    v=rel['version']; files={}; tok=''
    while True:
        j=req(f'{API}/{v["name"]}/files?pageSize1000'.replace('pageSize1000','pageSize=1000')+(f'&pageToken={tok}' if tok else ''))
        for f in j.get('files',[]): files[f['path']]=f['hash']
        tok=j.get('nextPageToken')
        if not tok: break
    return rel,v,files
def gz(b): return gzip.compress(b,9,mtime=0)
def publish(extra):  # extra: {path: bytes}
    rel,v,files=live(); blobs={}
    for p,b in extra.items():
        z=gz(b); h=hashlib.sha256(z).hexdigest(); files[p]=h; blobs[h]=z
    nv=req(f'{API}/sites/{P}/versions',{'config':v.get('config',{}),'labels':{'deployment-tool':'named-previews'}},'POST')
    pf=req(f'{API}/{nv["name"]}:populateFiles',{'files':files},'POST')
    for h in pf.get('uploadRequiredHashes',[]):
        if h not in blobs: raise SystemExit('live file needs re-upload, abort (no raw copy): '+h)
        req(f'{pf["uploadUrl"]}/{h}',blobs[h],'POST',{'Content-Type':'application/octet-stream'},raw=True)
    cur=req(f'{API}/sites/{P}/releases?pageSize=1')['releases'][0]
    if cur['name']!=rel['name']: raise SystemExit('live release moved during prepare; aborting, nothing released')
    req(f'{API}/{nv["name"]}?update_mask=status',{'status':'FINALIZED'},'PATCH')
    out=req(f'{API}/sites/{P}/releases?versionName={nv["name"]}',{},'POST')
    return out['name'],rel['name']
def title_of(pid):
    t=rtdb(f'pages/{pid}/title')
    if not t: raise SystemExit('page not found')
    return t
def have_stub(pid):
    try: urllib.request.urlopen(f'{HOST}/s/{slug(pid)}/'); return True
    except Exception: return False
a=sys.argv[1:]
if not a: raise SystemExit(__doc__)
if a[0]=='share':
    pid=a[1]
    if not re.fullmatch(r'[a-f0-9]{48}',pid): raise SystemExit('bad id')
    title=a[a.index('--title')+1] if '--title' in a else title_of(pid)
    extra={f's/{slug(pid)}/index.html':stub(pid,title).encode()}
    if os.path.exists(os.path.join(os.path.dirname(__file__),'og.jpg')) and 'og.jpg' not in live()[2] and '/og.jpg' not in live()[2]:
        extra['og.jpg']=open(os.path.join(os.path.dirname(__file__),'og.jpg'),'rb').read()
    r,old=publish({('/'+k):v for k,v in extra.items()}); print('released',r,'rollback',old); print(f'{HOST}/s/{slug(pid)}/')
elif a[0]=='rename':
    pid,title=a[1],a[2].strip()
    if not title or len(title)>100: raise SystemExit('title 1-100 chars')
    rtdb(f'pages/{pid}/title',title,'PUT'); rtdb(f'owned/{pid}/title',title,'PUT')
    if have_stub(pid): print(publish({f'/s/{slug(pid)}/index.html':stub(pid,title).encode()}))
    print('renamed')
elif a[0]=='put':  # put /hosting/path local_file : replace/add one file, everything else kept
    print(publish({a[1]:open(a[2],'rb').read()}))
elif a[0]=='list':
    for pid,v in (rtdb('owned') or {}).items(): print(pid[:8],v.get('mode'),v.get('title'),'STUB' if have_stub(pid) else '')
