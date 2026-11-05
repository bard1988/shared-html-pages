// Owner page list: shows the named share link (/s/<slug>/) next to each page when its preview stub exists.
// Read-only: HEAD request to the same site; no writes, no ACL change. Slug = sha256('preview:'+id)[:20].
(()=>{const H=async id=>{const d=await crypto.subtle.digest('SHA-256',new TextEncoder().encode('preview:'+id));return[...new Uint8Array(d)].map(b=>b.toString(16).padStart(2,'0')).join('').slice(0,20)};
const fill=async el=>{if(el.dataset.done)return;el.dataset.done='1';const u='/s/'+await H(el.dataset.id)+'/';let ok=false;try{ok=(await fetch(u,{method:'HEAD'})).ok}catch{}
el.innerHTML=ok?` \u00b7 <a href="${u}" target="_blank" rel="noreferrer">\u05e7\u05d9\u05e9\u05d5\u05e8 \u05e2\u05dd \u05e9\u05dd \u05dc\u05e9\u05d9\u05ea\u05d5\u05e3</a> <button class="secondary cpnl" data-u="${u}">\u05d4\u05e2\u05ea\u05e7\u05d4</button>`:' \u00b7 <small>\u05d0\u05d9\u05df \u05e2\u05d3\u05d9\u05d9\u05df \u05e7\u05d9\u05e9\u05d5\u05e8 \u05e2\u05dd \u05e9\u05dd (\u05d4\u05e2\u05d5\u05d6\u05e8 \u05d9\u05d5\u05e6\u05e8 \u05d1\u05d1\u05e7\u05e9\u05d4)</small>'};
new MutationObserver(()=>document.querySelectorAll('.nl').forEach(fill)).observe(document.documentElement,{childList:true,subtree:true});
document.addEventListener('click',e=>{const b=e.target.closest('.cpnl');if(b){navigator.clipboard.writeText(location.origin+b.dataset.u);b.textContent='\u05d4\u05d5\u05e2\u05ea\u05e7'}})})();
