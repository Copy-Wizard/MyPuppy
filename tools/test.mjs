import { chromium } from 'playwright';
const base='file://'+process.cwd();
const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium'});
const errs=[];
const MOCK=`window.supabase={createClient(){
  const ld=()=>JSON.parse(localStorage.getItem('mockdb')||'{"rows":{},"session":null}');const sv=d=>localStorage.setItem('mockdb',JSON.stringify(d));
  const row=()=>{const d=ld();return d.rows[d.session.user.id]};
  return {auth:{
    signUp:async({email})=>{const d=ld();d.session={user:{id:'u_'+email,email}};d.rows['u_'+email]=d.rows['u_'+email]||{state:null,photos:{},unlocked:false};sv(d);return{data:{session:d.session,user:d.session.user},error:null}},
    signInWithPassword:async({email,password})=>{const d=ld();if(!d.rows['u_'+email]||password!=='password1')return{data:{},error:{message:'Invalid login credentials'}};d.session={user:{id:'u_'+email,email}};sv(d);return{data:{session:d.session,user:d.session.user},error:null}},
    getSession:async()=>({data:{session:ld().session}}),onAuthStateChange(){},
    signOut:async()=>{const d=ld();d.session=null;sv(d);return{}},resetPasswordForEmail:async()=>({}),updateUser:async()=>({data:{user:ld().session.user}})},
   from(){return{update(v){return{eq(){const d=ld();Object.assign(d.rows[d.session.user.id],v);sv(d);return Promise.resolve({error:null})}}},select(){return{eq(){return{single:async()=>({data:row(),error:null})}}}}}},
   rpc:async()=>{if(localStorage.getItem('paid')){const d=ld();d.rows[d.session.user.id].unlocked=true;sv(d)}return{data:true}}}}};`;
async function mk(scheme,cloud){
  const ctx=await b.newContext({viewport:{width:400,height:820},colorScheme:scheme});
  const p=await ctx.newPage();
  p.on('console',m=>{if(m.type()==='error'&&!/ERR_|Failed to load/.test(m.text()))errs.push('console: '+m.text())});p.on('pageerror',e=>errs.push('PAGEERR '+e.message));
  await p.route('**/supabase.js',r=>cloud?r.fulfill({contentType:'text/javascript',body:MOCK}):r.abort());
  await p.route('**/fonts.googleapis.com/**',r=>r.abort());
  if(!cloud)await p.route('**/config.js',r=>r.fulfill({contentType:'text/javascript',body:'window.MYPUPPY_CONFIG={}'}));
  if(cloud)await p.route('**/config.js',r=>r.fulfill({contentType:'text/javascript',body:'window.MYPUPPY_CONFIG={supabaseUrl:"https://x.supabase.co",supabaseAnonKey:"k",gumroad:{pass:"https://x.gumroad.com/l/mypuppy",lifetime:"",monthly:""}}'}));
  return p;
}
const txt=p=>p.innerText('#app');
const ov=async(p,n)=>{const o=await p.evaluate(()=>document.documentElement.scrollWidth-window.innerWidth);if(o>0)errs.push('overflow '+n+' '+o)};
async function onboard(p){
  await p.click('[data-go="1"]');await p.fill('#f-name','Max');await p.selectOption('#f-gender','male');await p.click('[data-go="2"]');
  await p.click('[data-c="biting"]');await p.click('[data-go="3"]');await p.fill('#f-story','We adopted Max from a neighbour whose dog had six puppies.');await p.click('[data-go="4"]');
}
const tickAll=async p=>{const n=await p.locator('input[data-task]').count();for(let i=0;i<n;i++)await p.locator('input[data-task]').nth(i).click()};

// ---- local mode ----
{const p=await mk('light',false);await p.goto(base+'/app/index.html');
 if(await p.$('#go-signin'))errs.push('local: signin shown');
 await onboard(p);await p.click('#finish');let t=await txt(p);if(!t.includes('Day 1 of 90'))errs.push('local: no day1');
 await tickAll(p);await p.click('[data-tab="help"]');if(!(await p.$('#t-next')))errs.push('local: no test tools');
 await p.click('#t-next');await p.click('[data-tab="help"]');await p.click('#t-next');t=await txt(p);
 if(!/last free day/i.test(t))errs.push('local: no last-free-day banner');
 await p.click('#seeplans');if(!(await p.$('#unlock')))errs.push('local: no test unlock');
 await p.screenshot({path:'tools/shots/local-day3.png',fullPage:true});await ov(p,'local');await p.context().close();}

// ---- cloud mode (mocked) ----
for(const scheme of ['light','dark']){const p=await mk(scheme,true);await p.goto(base+'/app/index.html');
 if(!(await p.$('#go-signin')))errs.push('cloud: no signin button');
 await onboard(p);await p.click('[data-go="5"]');
 if(!(await p.$('#signup')))errs.push('cloud: no signup step');
 await p.screenshot({path:`tools/shots/${scheme}-signup.png`,fullPage:true});await ov(p,'signup');
 await p.fill('#a-email','bad');await p.click('#signup');if(!(await p.$('#signup')))errs.push('cloud: bad email accepted');
 await p.fill('#a-email','ali@example.com');await p.fill('#a-pass','password1');await p.click('#signup');
 await p.waitForSelector('.daypill');let t=await txt(p);if(!t.includes('Day 1 of 90'))errs.push('cloud: no day1');
 await tickAll(p);await p.waitForTimeout(900);
 let db=await p.evaluate(()=>JSON.parse(localStorage.getItem('mockdb')));const r=db.rows['u_ali@example.com'];
 if(!r.state||r.state.profile.name!=='Max'||r.puppy_name!=='Max'||r.cur_day!==1)errs.push('cloud: not pushed '+JSON.stringify(r).slice(0,200));
 if('unlocked' in r.state)errs.push('cloud: unlocked leaked into state');
 await p.click('[data-tab="help"]');if(await p.$('#t-next'))errs.push('cloud: test tools visible');
 if(!(await p.$('#signout')))errs.push('cloud: no signout');
 // move the saved state to day 3 complete (as if 2 days passed), then reload = pull from cloud
 await p.evaluate(()=>{const d=JSON.parse(localStorage.getItem('mockdb'));const s=d.rows['u_ali@example.com'].state;const day=n=>{const x=new Date();x.setDate(x.getDate()-n);return x.getFullYear()+'-'+String(x.getMonth()+1).padStart(2,'0')+'-'+String(x.getDate()).padStart(2,'0')};
   s.cur=3;s.done[2]=s.done[1];s.doneOn={1:day(2),2:day(1)};s.last=day(1);s.rev=999;localStorage.setItem('mockdb',JSON.stringify(d));localStorage.removeItem('mypuppy-v2')});
 await p.reload();await p.waitForSelector('.daypill');t=await txt(p);
 if(!t.includes('Day 3 of 90'))errs.push('cloud: pull failed '+t.slice(0,80));
 if(!/last free day/i.test(t))errs.push('cloud: no last-day banner');
 await tickAll(p);t=await txt(p);if(!/free preview complete/i.test(t))errs.push('cloud: no paywall');
 const href=await p.getAttribute('a.plan','href');if(href!=='https://x.gumroad.com/l/mypuppy?wanted=true&email=ali%40example.com')errs.push('cloud: bad buy link '+href);
 if((await p.locator('a.plan').count())!==1)errs.push('cloud: plan count');
 await p.screenshot({path:`tools/shots/${scheme}-paywall.png`,fullPage:true});await ov(p,'paywall');
 await p.click('#refresh-access');await p.waitForTimeout(300);if(!/free preview complete/i.test(await txt(p)))errs.push('cloud: unlocked without paying');
 await p.evaluate(()=>localStorage.setItem('paid','1'));await p.click('#refresh-access');await p.waitForTimeout(400);
 t=await txt(p);if(/free preview complete/i.test(t)||!t.includes('Day 4 opens tomorrow'))errs.push('cloud: not unlocked after pay: '+t.slice(0,300));
 // sign out, wrong password, sign in
 await p.click('[data-tab="help"]');await p.click('#signout');await p.waitForSelector('#go-signin');
 if(await p.evaluate(()=>localStorage.getItem('mypuppy-v2')&&JSON.parse(localStorage.getItem('mypuppy-v2')).profile))errs.push('cloud: local data kept after signout');
 await p.click('#go-signin');await p.fill('#a-email','ali@example.com');await p.fill('#a-pass','wrong');await p.click('#signin');await p.waitForTimeout(200);
 if(!(await p.$('#signin')))errs.push('cloud: wrong password accepted');
 await p.fill('#a-pass','password1');await p.click('#signin');await p.waitForSelector('.daypill');t=await txt(p);
 if(!t.includes('Max')||!t.includes('Day 3 of 90'))errs.push('cloud: signin restore failed');
 await p.context().close();}

// ---- landing ----
for(const [w,n] of [[400,'phone'],[1200,'desk']]){const ctx=await b.newContext({viewport:{width:w,height:900}});const p=await ctx.newPage();await p.route('**/fonts.googleapis.com/**',r=>r.abort());
 await p.goto(base+'/index.html');await ov(p,'landing-'+n);await p.screenshot({path:`tools/shots/landing-${n}.png`,fullPage:true});
 const links=await p.$$eval('a.btn',a=>a.map(x=>x.getAttribute('href')));if(!links.every(h=>h==='app/'))errs.push('landing links '+links);await ctx.close();}
console.log(errs.length?errs.join('\n'):'ALL OK');await b.close();
