import fs from 'node:fs';import crypto from 'node:crypto';import{execFileSync}from'node:child_process';
// Uses the current Firebase CLI's own authenticated session. Never supply tokens.
const [op,idOrFile,contentFile]=process.argv.slice(2),project=process.env.FIREBASE_PROJECT;
if(!project)throw Error('Set FIREBASE_PROJECT to your Firebase project id');
const cli=process.env.FIREBASE_CLI||'firebase';
function run(args){return execFileSync(cli,[...args,'--project',project],{encoding:'utf8'})}
if(op==='create'){
 const p=JSON.parse(fs.readFileSync(idOrFile,'utf8'));if(!p.title||(!p.html&&p.type!=='list')||!['google','public'].includes(p.mode))throw Error('title/html/mode required; password pages use owner UI');if(p.type!==undefined&&p.type!=='list')throw Error('Unknown page type');
 if(p.title.length>100||(p.html||'').length>100000)throw Error('Content exceeds limits');for(const email of [...(p.readers||[]),...(p.editors||[])])if(!/^\S+@\S+\.\S+$/.test(email)||email.includes('|'))throw Error('Invalid exact email');
 const id=crypto.randomBytes(24).toString('hex');const policy={mode:p.mode,readers:'|'+(p.readers||[]).map(x=>x.toLowerCase()).join('|')+'|',editors:'|'+(p.editors||[]).map(x=>x.toLowerCase()).join('|')+'|',publicEdit:p.mode==='public'&&p.publicEdit===true};
 // Four narrow writes; policy first, metadata last, never overwrite a parent list.
 for(const[path,data]of[[`/policies/${id}`,policy],[`/pages/${id}`,{title:p.title,html:p.html||'',state:{_ready:true},...(p.type?{type:p.type}:{})}],[`/owned/${id}`,{title:p.title,mode:p.mode,createdAt:Date.now()}],[`/meta/${id}`,{mode:p.mode}]])run(['database:set',path,'--data',JSON.stringify(data),'--force']);
 console.log('https://'+project+'.web.app/#p='+id);
}else if(op==='revise'){
 if(!/^[a-f0-9]{48}$/.test(idOrFile))throw Error('Exact existing page ID required');const html=fs.readFileSync(contentFile,'utf8');if(html.length>100000)throw Error('HTML too large');const previous=JSON.parse(run(['database:get',`/pages/${idOrFile}`]));if(!previous?.html)throw Error('Page not found');run(['database:set',`/pages/${idOrFile}/html`,'--data',JSON.stringify(html),'--force']);console.log('Updated existing page; state and audience unchanged.');
}else if(op==='set-type'){
 if(!/^[a-f0-9]{48}$/.test(idOrFile))throw Error('Exact existing page ID required');const previous=JSON.parse(run(['database:get',`/pages/${idOrFile}`]));if(!previous?.title)throw Error('Page not found');
 if(contentFile==='list'){run(['database:set',`/pages/${idOrFile}/type`,'--data','"list"','--force']);console.log('Page type set to list; stored html kept as snapshot.')}
 else if(contentFile==='none'){run(['database:remove',`/pages/${idOrFile}/type`,'--force']);console.log('Page type removed; stored html renders again.')}
 else throw Error('set-type accepts list|none');
}else throw Error('Usage: node admin-page.mjs create page.json | revise PAGE_ID page.html | set-type PAGE_ID list|none');
