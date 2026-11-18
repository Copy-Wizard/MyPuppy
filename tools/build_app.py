"""Builds app/index.html from the prototype file. Run: python3 tools/build_app.py <prototype.html>"""
import sys, pathlib
src = pathlib.Path(sys.argv[1]).read_text()
root = pathlib.Path(__file__).resolve().parent.parent

def rep(s, old, new, count=1):
    assert s.count(old) == count, (old[:70], s.count(old))
    return s.replace(old, new)

head, script = src.split('<script>\n', 1)
script = script.rsplit('</script>', 1)[0]
markup = head.split('</style>', 1)[1]
css = head.split('<style>', 1)[1].split('</style>', 1)[0]

css += """
input[type=password]{font:400 15px var(--font-body);padding:11px 12px;border-radius:10px;border:1px solid var(--line);background:var(--surface);color:var(--ink);width:100%}
.wrap a.plan{text-decoration:none;color:inherit}
a.plan:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.wrap a{color:var(--accent)}
"""

# ---------- cloud layer ----------
script = rep(script, "function persist(){mem=S;try{localStorage.setItem(KEY,JSON.stringify(S))}catch(e){}}",
             "function persist(){S.rev=(S.rev||0)+1;mem=S;try{localStorage.setItem(KEY,JSON.stringify(S))}catch(e){}pushCloud()}")
script = rep(script, "function savePhotos(){pmem=PH;try{", "function savePhotos(){pmem=PH;pushCloud();try{")
script = rep(script, "let PH=loadPhotos()||{};\n", """let PH=loadPhotos()||{};
/* ---------- accounts and cloud save (Supabase). With no settings in config.js the app runs on this device only. ---------- */
const CFG=window.MYPUPPY_CONFIG||{};
const cloud=(CFG.supabaseUrl&&CFG.supabaseAnonKey&&window.supabase)?window.supabase.createClient(CFG.supabaseUrl,CFG.supabaseAnonKey):null;
let user=null,pushT=null,authMode=null,authNote='';
function pushCloud(){
  if(!cloud||!user||!S.profile)return;
  clearTimeout(pushT);pushT=setTimeout(flushCloud,700);
}
function flushCloud(){
  clearTimeout(pushT);pushT=null;
  if(!cloud||!user||!S.profile)return;
  const state=Object.assign({},S);delete state.unlocked;delete state.previewDay;
  cloud.from('profiles').update({state,photos:PH,puppy_name:S.profile.name,cur_day:S.cur,last_active:S.last,updated_at:new Date().toISOString()}).eq('id',user.id).then(r=>{if(r&&r.error)console.error(r.error)},e=>console.error(e));
}
async function pullCloud(){
  if(!cloud||!user)return;
  try{
    const {data,error}=await cloud.from('profiles').select('state,photos,unlocked').eq('id',user.id).single();
    if(error||!data)return;
    /* take the saved copy unless this device holds newer, unsent changes */
    if(data.state&&data.state.profile&&!(S.profile&&(S.rev||0)>(data.state.rev||0))){S=Object.assign(blank(),data.state);PH=data.photos||{};pmem=PH;try{localStorage.setItem(PKEY,JSON.stringify(PH))}catch(e){}}
    delete S.pendingSignup;
    S.unlocked=!!data.unlocked;
    persist();
  }catch(e){console.error(e)}
}
async function refreshAccess(quiet){
  if(!cloud||!user)return;
  try{await cloud.rpc('claim_purchase')}catch(e){}
  const was=S.unlocked;
  try{const {data}=await cloud.from('profiles').select('state,photos,unlocked').eq('id',user.id).single();if(data){S.unlocked=!!data.unlocked;persist()}}catch(e){}
  render();
  if(!quiet||(!was&&S.unlocked))toast(S.unlocked?'Full plan unlocked':'No payment found yet for this email. It can take a minute.');
}
const validEmail=v=>/^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test(v);
const val=id=>{const el=document.getElementById(id);return el?el.value.trim():''};
""")

# ---------- onboarding: account step ----------
script = rep(script, "const OB_STEPS=5;", "const obSteps=()=>cloud&&!user?6:5;")
script = script.replace("OB_STEPS", "obSteps()")
script = rep(script, """<div class="stack"><button class="btn btn-primary btn-block" data-go="1">Set up my puppy</button></div></div>`;""",
             """<div class="stack"><button class="btn btn-primary btn-block" data-go="1">Set up my puppy</button>${cloud?'<button class="btn btn-block" id="go-signin">I already have an account</button>':''}</div></div>`;""")
script = rep(script, "  const nav=st>0?", """  if(st===5)body=`<div class="stack"><h2>Save ${nm}'s plan</h2>
    <p class="muted">Create your free account so ${nm}'s progress is saved and works on any device. Daily reminders go to this email.</p>
    <label class="f">Email<input id="a-email" type="email" autocomplete="email" value="${esc(d.email||'')}"></label>
    <label class="f">Password <span class="muted small">At least 8 characters</span><input id="a-pass" type="password" autocomplete="new-password"></label>
    <p class="small muted">By creating an account you agree to the <a href="../#terms">terms, refund policy and privacy policy</a>.</p></div>`;
  const nav=st>0?""")
script = rep(script, """${st===obSteps()-1?'id="finish"':`data-go="${st+1}"`}>${st===obSteps()-1?'Start Day 1':'Next'}</button>""",
             """${st===obSteps()-1?(cloud&&!user?'id="signup"':'id="finish"'):`data-go="${st+1}"`}>${st===obSteps()-1?(cloud&&!user?'Create account and start':'Start Day 1'):'Next'}</button>""")
script = rep(script, "function renderOb(){\n  $('#tabs').hidden=true;\n", """function renderAuth(){
  $('#tabs').hidden=true;
  if(authMode==='newpass'){$('#app').innerHTML=`<div class="stack-lg"><div class="stack"><p class="eyebrow">MyPuppy</p><h1>Set a new password</h1></div>
    <div class="stack"><label class="f">New password <span class="muted small">At least 8 characters</span><input id="a-pass" type="password" autocomplete="new-password"></label>
    <button class="btn btn-primary btn-block" id="setpass">Save password</button></div></div>`;return}
  $('#app').innerHTML=`<div class="stack-lg"><div class="stack"><p class="eyebrow">MyPuppy</p><h1>Welcome back</h1>${authNote?`<div class="note">${esc(authNote)}</div>`:''}</div>
    <div class="stack"><label class="f">Email<input id="a-email" type="email" autocomplete="email"></label>
    <label class="f">Password<input id="a-pass" type="password" autocomplete="current-password"></label>
    <button class="btn btn-primary btn-block" id="signin">Sign in</button>
    <div class="row" style="justify-content:space-between"><button class="btn btn-ghost" id="forgot">Forgot password</button>${P()?'':'<button class="btn btn-ghost" id="back-welcome">Back</button>'}</div></div></div>`;
}
function renderOb(){
  $('#tabs').hidden=true;
  if(cloud&&(authMode==='newpass'||(!user&&(authMode==='signin'||P())))){renderAuth();return}
""")
script = rep(script, "function finishOb(){\n  const d=ob.data;S=blank();", "function finishOb(pending){\n  const d=ob.data;S=blank();if(pending)S.pendingSignup=true;")
script = rep(script, "function grabOb(){const g=id=>{const el=document.getElementById(id);return el?el.value:undefined};",
             "function grabOb(){const g=id=>{const el=document.getElementById(id);return el?el.value:undefined};const em=g('a-email');if(em!==undefined)ob.data.email=em;")

# ---------- paywall ----------
a = script.index("function paywall(){")
b = script.index("Send me the offer</button></div>`}") + len("Send me the offer</button></div>`}")
script = script[:a] + """function buyLink(u){const e=user&&user.email?encodeURIComponent(user.email):'';return u+(u.includes('?')?'&':'?')+'wanted=true'+(e?'&email='+e:'')}
function paywall(){
  const n=esc(P().name),early=!complete(S.cur),g=CFG.gumroad||{};
  const plan=(k,name,line,price,main)=>g[k]?`<a class="plan ${main?'main':''}" href="${esc(buyLink(g[k]))}" target="_blank" rel="noopener"><span><b>${name}</b><br><span class="small muted">${line}</span></span><span class="price">${price}</span></a>`:'';
  const plans=plan('pass','90-Day Pass','The full plan, paid once','$29',true)+plan('monthly','Monthly','Cancel any time','$9.99')+plan('lifetime','Lifetime','Includes future modules','$59');
  let buy;
  if(plans)buy=`<div class="plans">${plans}</div>
    <p class="small muted">Checkout opens on Gumroad. Use the same email as your MyPuppy account${user?' ('+esc(user.email)+')':''}. 7-day refund.</p>
    <button class="btn btn-block" id="refresh-access">I've paid. Unlock my plan</button>`;
  else if(cloud)buy=`<div class="note">Paid plans open soon. We will email ${user?esc(user.email):'you'} when they do. ${n}'s progress is saved.</div>`;
  else buy=`<button class="btn btn-primary btn-block" id="unlock">Unlock for testing</button>`;
  return `<div class="card stack" id="paywall"><p class="eyebrow">${early?'Last free day':'Free preview complete'}</p><h2>Keep going with ${n}</h2>
  <p class="small">${early?'Today is the last free day. Upgrade now and Day 4 opens tomorrow without a break.':'You finished the 3 free days.'} The full plan has 87 more days of tasks, coach messages, trackers and weekly check-ins, ending with ${n}'s graduation certificate.</p>
  ${buy}</div>`}""" + script[b:]

# ---------- help tab ----------
a = script.index('  <div class="card stack"><h3>Testing tools</h3>')
b = script.index("""${S.unlocked?'<button class="btn" id="t-lock">Lock the plan again</button>':''}</div>""") + len("""${S.unlocked?'<button class="btn" id="t-lock">Lock the plan again</button>':''}</div>""")
testing = script[a:b]
script = script[:a] + """  ${cloud&&user?`<div class="card stack"><h3>Your account</h3><p class="small">Signed in as ${esc(user.email)}. Your progress is saved to your account.</p><div class="row"><button class="btn" id="signout">Sign out</button>${S.unlocked?'':'<button class="btn" id="refresh-access">I\\'ve paid. Unlock my plan</button>'}</div></div>`:''}
  ${cloud?'':`""" + testing.strip() + """`}""" + script[b:]
script = rep(script, " In this prototype, everything stays on this device.", " Your data is stored with our database provider, Supabase.")
script = rep(script, """\n    <p class="small muted" style="margin-top:8px">Draft wording. Have it reviewed before launch.</p>""", "")
script = rep(script, "photos and all tracking on this device.", "photos and all tracking. Your account stays.")
script = rep(script, "from Help, under Start over, or by emailing", "from Help, under Start over. To delete your account, email")

# ---------- render + events ----------
script = rep(script, "function render(){\n  if(!P()){renderOb();return}", "function render(){\n  if(!P()||(cloud&&!user)||authMode==='newpass'){renderOb();return}")
script = rep(script, "  if(t.id==='finish'){grabOb();finishOb();return}", """  if(t.id==='finish'){grabOb();finishOb();return}
  if(t.id==='go-signin'){authMode='signin';authNote='';renderOb();return}
  if(t.id==='back-welcome'){authMode=null;renderOb();return}
  if(t.id==='signup'){grabOb();const em=val('a-email'),pw=(document.getElementById('a-pass')||{}).value||'';
    if(!validEmail(em)){toast('Enter a valid email address');return}
    if(pw.length<8){toast('Use a password of at least 8 characters');return}
    t.disabled=true;
    cloud.auth.signUp({email:em,password:pw}).then(({data,error})=>{
      if(error){t.disabled=false;toast(error.message);return}
      if(data.session){user=data.user;authMode=null;finishOb();refreshAccess(true)}
      else{authMode='signin';authNote='Check your email to confirm your account, then sign in here.';finishOb(true)}
    },()=>{t.disabled=false;toast('Could not reach the server. Try again.')});return}
  if(t.id==='signin'){const em=val('a-email'),pw=(document.getElementById('a-pass')||{}).value||'';
    if(!validEmail(em)||!pw){toast('Enter your email and password');return}
    t.disabled=true;
    cloud.auth.signInWithPassword({email:em,password:pw}).then(async({data,error})=>{
      if(error){t.disabled=false;toast(error.message);return}
      user=data.user;authMode=null;authNote='';await pullCloud();checkAway();tab='today';render();
    },()=>{t.disabled=false;toast('Could not reach the server. Try again.')});return}
  if(t.id==='forgot'){const em=val('a-email');if(!validEmail(em)){toast('Enter your email first');return}
    cloud.auth.resetPasswordForEmail(em,{redirectTo:location.origin+location.pathname}).then(()=>toast('If that email has an account, a reset link is on its way.'));return}
  if(t.id==='setpass'){const pw=(document.getElementById('a-pass')||{}).value||'';if(pw.length<8){toast('Use a password of at least 8 characters');return}
    cloud.auth.updateUser({password:pw}).then(async({data,error})=>{if(error){toast(error.message);return}user=data.user;authMode=null;await pullCloud();render();toast('Password saved')});return}
  if(t.id==='signout'){cloud.auth.signOut().then(()=>{user=null;S=blank();PH={};mem=S;pmem=PH;try{localStorage.removeItem(KEY);localStorage.removeItem(PKEY)}catch(e){}ob={step:0,data:{concerns:[]},photo:null};authMode=null;tab='today';render()});return}
  if(t.id==='refresh-access'){t.disabled=true;refreshAccess(false);return}""")
script = rep(script, "  if(t.id==='unlock'){S.unlocked=true;", "  if(t.id==='unlock'){if(cloud)return;S.unlocked=true;")
script = rep(script, "checkAway();persist();\nrender();\n})();", """async function boot(){
  if(cloud){
    try{
      cloud.auth.onAuthStateChange(ev=>{if(ev==='PASSWORD_RECOVERY'){authMode='newpass';render()}});
      const {data}=await cloud.auth.getSession();
      if(data&&data.session){user=data.session.user;await pullCloud()}
      else if(S.profile&&!S.pendingSignup){S=blank();PH={}}
      else if(S.pendingSignup){authMode='signin'}
    }catch(e){console.error(e)}
    window.addEventListener('focus',()=>{if(user&&P()&&!S.unlocked)refreshAccess(true)});
    document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='hidden'&&pushT)flushCloud()});
  }
  checkAway();persist();render();
}
boot();
})();""")

title_and_fonts = head.split('<style>', 1)[0]
html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="robots" content="noindex">
<link rel="icon" href="../assets/icon.svg" type="image/svg+xml">
<meta name="theme-color" content="#1C6B5E">
{title_and_fonts.strip()}
<style>
body{{margin:0}}img{{max-width:100%}}[hidden]{{display:none!important}}
{css.strip()}
</style>
</head>
<body>
{markup.strip()}
<script src="../config.js"></script>
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/supabase.js"></script>
<script>
{script}</script>
</body>
</html>
"""
(root / 'app' / 'index.html').write_text(html)
(root / 'tools' / '_app.js').write_text(script)
print('built', len(html))
