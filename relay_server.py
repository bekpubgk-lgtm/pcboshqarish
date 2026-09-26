"""Relay v3 - sensor (touch) boshqaruvi, tez ekran oqimi, tugmalar yashirin.
Mahalliy ishlatish: python relay_server.py  (yoki relay_server_v3.exe)
Telefon brauzeridan: http://<PC-LAN-IP>:8888
"""
import json, time, base64, os, socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

def lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

PORT = int(os.environ.get("PORT", "8888"))
PAIR_CODE = os.environ.get("PAIR_CODE", "PC-2026-77AA")
MAXQ = 300
inbox = {}
seen = {}
latest_img = {"data": b"", "v": 0}
agent_ts = {"t": 0.0}
P1 = """<!DOCTYPE html><html><head><meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no,viewport-fit=cover'>
<title>PC Remote</title><style>
html,body{margin:0;height:100%;background:#000;color:#eee;font-family:sans-serif;overflow:hidden}
#stage{position:fixed;inset:0;overflow:hidden;touch-action:none}
#scr{position:absolute;left:0;top:0;transform-origin:0 0;will-change:transform;display:none}
#hud{position:fixed;top:6px;left:8px;font-size:11px;color:#7f7;background:rgba(0,0,0,.55);padding:4px 9px;border-radius:8px;z-index:5}
#fab{position:fixed;right:14px;bottom:20px;width:54px;height:54px;border-radius:50%;background:rgba(40,40,40,.85);border:1px solid #666;color:#fff;font-size:22px;z-index:6}
#fit{position:fixed;right:14px;bottom:84px;width:42px;height:42px;border-radius:50%;background:rgba(40,40,40,.85);border:1px solid #666;color:#fff;font-size:15px;z-index:6}
#drawer{position:fixed;left:0;right:0;bottom:0;background:#161616;border-top:1px solid #333;padding:10px;display:none;z-index:7;max-height:66%;overflow:auto}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:6px}
.grid2{display:grid;grid-template-columns:repeat(2,1fr);gap:6px}
button{background:#2d2d2d;color:#fff;border:0;border-radius:10px;padding:12px 0;font-size:14px}
button:active{background:#666}
input{width:100%;padding:12px;border-radius:9px;border:0;font-size:15px;margin:0 0 7px 0}
#lock{position:fixed;inset:0;background:#111;display:flex;flex-direction:column;gap:9px;align-items:center;justify-content:center;z-index:9}
#lock input{padding:13px;font-size:17px;border-radius:10px;border:0;width:240px;text-align:center;margin:0}
#files div{padding:9px;background:#1d1d1d;margin:4px 0;border-radius:8px;font-size:13px}
h3{margin:8px 2px 5px;font-size:12px;color:#999}
.hint{position:fixed;left:50%;top:50%;transform:translate(-50%,-50%);text-align:center;color:#666;font-size:13px;line-height:1.7}
</style></head><body>
<div id='lock'><h2>PC Remote</h2>
<input id='srv' placeholder='server (bosh = shu sayt)'>
<input id='pin' type='password' placeholder='Kod'>
<button onclick='login()' style='width:240px;padding:14px'>Kirish</button></div>
<div id='stage'>
 <img id='scr' alt=''>
 <div class='hint' id='hint'>Boshlash uchun kodni kiriting<br>Keyin ekran shu yerda chiqadi</div>
</div>
<div id='hud'>ulanmagan</div>
<button id='fit'>&#9634;</button>
<button id='fab'>&#9776;</button>
<div id='drawer'>
 <h3>KLAVIATURA</h3>
 <input id='txt' placeholder='Matn yozing (mikrofon ham ishlaydi)'>
 <div class='grid'>
  <button id='k_send'>Yuborish</button><button id='k_enter'>Enter</button>
  <button id='k_esc'>Esc</button><button id='k_tab'>Tab</button>
  <button id='k_bs'>&#9003;</button><button id='k_copy'>Copy</button>
  <button id='k_paste'>Paste</button><button id='k_altab'>Alt+Tab</button>
  <button id='k_win'>Win</button><button id='k_winl'>Win+L</button>
  <button id='k_up'>PgUp</button><button id='k_dn'>PgDn</button>
 </div>
 <h3>OVOZ</h3>
 <div class='grid'>
  <button id='k_volup'>Vol+</button><button id='k_voldn'>Vol-</button>
  <button id='k_mute'>Mute</button><button id='k_play'>Play</button>
 </div>
 <h3>ILOVALAR</h3>
 <div class='grid' id='apps'></div>
 <h3>FAYLLAR</h3>
 <input id='fpath' placeholder='papka (bosh = uy papkasi)'>
 <div class='grid2'>
  <button id='ls'>Ko'rish</button><button id='home'>Uy papkasi</button>
 </div>
 <div id='files'></div>
 <h3>TIZIM</h3>
 <div class='grid2'>
  <button id='shut' style='background:#7a2020'>Ochirish</button>
  <button id='reb' style='background:#7a2020'>Qayta yuklash</button>
 </div>
</div>
<script>
var SRV='',CODE='';
"""
P2 = """function hud(t){document.getElementById('hud').textContent=t}
function req(path,body,ms){
 ms=ms||15000;
 var url=(path.charAt(0)==='/'&&(SRV===''||SRV===window.location.origin))?path:(SRV+path);
 return new Promise(function(res,rej){
  var d=false,t=setTimeout(function(){if(!d){d=true;rej(new Error('timeout'))}},ms);
  fetch(url,{method:body?'POST':'GET',headers:{'Content-Type':'application/json'},
   body:body?JSON.stringify(body):undefined})
  .then(function(r){if(!d){d=true;clearTimeout(t);res(r)}})
  .catch(function(e){if(!d){d=true;clearTimeout(t);rej(e)}});
 });}
var pid=0;
function cmd(c){req('/send',{code:CODE,from:'phone',to:'pc',cmd:c},12000)
 .catch(function(e){hud('xato: '+e.message)});}
function poll(){
 req('/poll?code='+encodeURIComponent(CODE)+'&who=phone&since='+pid,null,35000)
 .then(function(r){return r.json()})
 .then(function(d){
   var mx=pid;
   (d.msgs||[]).forEach(function(m){mx=Math.max(mx,m.id);
     var c=m.cmd||{};
     if(c.t==='files_res'){showFiles(c);}
     if(c.t==='info'&&c.w){SW=c.w;SH=c.h;}});
   if(mx>pid){req('/ack',{code:CODE,who:'phone',upto:mx},8000).catch(function(){});pid=mx;}
   poll();
 }).catch(function(){setTimeout(poll,2500)});
}
var SW=0,SH=0;
function login(){
 var s=document.getElementById('srv').value.trim();
 if(s){SRV=s;if(SRV.slice(-1)==='/'){SRV=SRV.slice(0,-1);}}else{SRV=window.location.origin;}
 CODE=document.getElementById('pin').value.trim();
 if(!CODE){alert('Kodni kiriting');return;}
 req('/send',{code:CODE,from:'phone',to:'pc',cmd:{t:'ping'}},12000)
 .then(function(r){if(!r.ok){throw new Error('kod xato');}return r.json();})
 .then(function(){
   document.getElementById('lock').style.display='none';
   poll();frame();
 }).catch(function(e){alert('Ulanmadi: '+e.message)});
}


var scr=document.getElementById('scr'),stage=document.getElementById('stage');
var vS=1,vX=0,vY=0,imgV=0,fpsN=0,fpsT=Date.now(),failN=0;
function base(){
 var r=stage.getBoundingClientRect();
 return {l:r.left+scr.offsetLeft,t:r.top+scr.offsetTop,w:scr.clientWidth||1,h:scr.clientHeight||1};
}
function apply(){scr.style.transform='translate('+vX+'px,'+vY+'px) scale('+vS+')';}
function fitView(){vS=1;vX=0;vY=0;apply();}
function clampView(){
 var b=base();
 var minX=b.l+(b.w-b.w*vS), maxX=b.l;
 var minY=b.t+(b.h-b.h*vS), maxY=b.t;
 if(vS<=1.001){vX=0;vY=0;return;}
 vX=Math.max(minX,Math.min(maxX,vX));
 vY=Math.max(minY,Math.min(maxY,vY));
}
function frac(px,py){
 var b=base();
 var Lx=(px-(b.l+vX))/vS, Ly=(py-(b.t+vY))/vS;
 return {x:Lx/b.w,y:Ly/b.h,lx:Lx,ly:Ly,b:b};
}
function frame(){
 req('/img?code='+encodeURIComponent(CODE)+'&v='+imgV,null,12000)
 .then(function(r){
  if(r.status===304){return null;}
  var hv=r.headers.get('X-Version');
  if(hv){imgV=parseInt(hv,10)||imgV;}
  if(!r.ok){throw new Error('img '+r.status);}
  return r.blob();
 })
 .then(function(b){
  if(b){
   var old=scr.getAttribute('durl');
   var nu=URL.createObjectURL(b);
   scr.src=nu;scr.setAttribute('durl',nu);
   if(old){setTimeout(function(){URL.revokeObjectURL(old)},2000);}
   if(scr.style.display!=='block'){
     scr.style.display='block';
     var h=document.getElementById('hint');if(h){h.style.display='none';}
   }
  }
  fpsN++;var n=Date.now();
  if(n-fpsT>1500){
    var age=SH?('  PC '+SW+'x'+SH):'';
    hud(Math.round(fpsN*1000/(n-fpsT))+' fps'+age+(vS>1.01?('  x'+vS.toFixed(1)):''));
    fpsN=0;fpsT=n;}
  failN=0;
  setTimeout(frame,(b?60:280));
 }).catch(function(){
  failN++;
  if(failN%8===1){hud('ulanish kutilmoqda...');}
  setTimeout(frame,Math.min(4000,400+failN*250));
 });
}
var tState={};
function newState(mode){return {mode:mode,x0:0,y0:0,px:0,py:0,t0:0,moved:0,down:false,rc:false,d0:0,m0:null,sc:0,lastSc:0};}
var G=newState('idle'),longT=null,lastTap=0;
function dist(a,b){var dx=a.clientX-b.clientX,dy=a.clientY-b.clientY;return Math.sqrt(dx*dx+dy*dy);}
function mid(a,b){return {x:(a.clientX+b.clientX)/2,y:(a.clientY+b.clientY)/2};}
function clearLong(){if(longT){clearTimeout(longT);longT=null;}}
stage.addEventListener('touchstart',function(e){
 e.preventDefault();
 if(e.touches.length===2){
  clearLong();
  if(G.mode==='one'&&G.moved===0&&G.mode!=='drag'){}
  G=newState('pinch');
  G.d0=dist(e.touches[0],e.touches[1]);
  G.m0=mid(e.touches[0],e.touches[1]);
  var bb=base();
  G.lx0=(G.m0.x-(bb.l+vX))/vS;
  G.ly0=(G.m0.y-(bb.t+vY))/vS;
  G.b=bb;G.s0=vS;G.vX0=vX;G.vY0=vY;
  return;
 }
 if(e.touches.length===1){
  var t=e.touches[0];
  G=newState('one');
  G.x0=t.clientX;G.y0=t.clientY;G.px=t.clientX;G.py=t.clientY;
  G.t0=Date.now();G.moved=0;G.f=frac(t.clientX,t.clientY);
  longT=setTimeout(function(){
   if(G.mode==='one'&&G.moved<14){
     G.rc=true;
     cmd({t:'mouse',a:'rtap',fx:G.f.x,fy:G.f.y});
     clearLong();
   }
  },620);
 }
},{passive:false});


stage.addEventListener('touchmove',function(e){
 e.preventDefault();
 if(G.mode==='pinch'&&e.touches.length>=2){
  var d=dist(e.touches[0],e.touches[1]);
  var m=mid(e.touches[0],e.touches[1]);
  var ratio=(G.d0>0)?(d/G.d0):1;
  var dy=Math.abs(m.y-G.m0.y);
  if(Math.abs(d-G.d0)<18&&dy>10){
   G.sc+=(m.y-G.m0.y);
   var steps=Math.round(G.sc/26);
   if(steps!==0){
     cmd({t:'mouse',a:'scrollat',n:steps*3,
          fx:Math.max(0,Math.min(1,G.lx0/G.b.w)),
          fy:Math.max(0,Math.min(1,G.ly0/G.b.h))});
     G.sc=0;
   }
   G.m0=m;
   return;
  }
  var s=Math.max(1,Math.min(8,G.s0*ratio));
  vS=s;
  vX=m.x-G.b.l-s*((G.m0.x-(G.b.l+G.vX0))/G.s0);
  vY=m.y-G.b.t-s*((G.m0.y-(G.b.t+G.vY0))/G.s0);
  clampView();
  apply();
  return;
 }
 if(G.mode==='one'&&e.touches.length===1){
  var t=e.touches[0];
  var dx=t.clientX-G.px, dy=t.clientY-G.py;
  G.moved=Math.max(G.moved,Math.abs(t.clientX-G.x0)+Math.abs(t.clientY-G.y0));
  if(G.moved>14){clearLong();}
  if(vS>1.01){
   if(G.moved>6){vX+=dx;vY+=dy;clampView();apply();}
  }else if(G.mode==='drag'){
   var f2=frac(t.clientX,t.clientY);
   cmd({t:'mouse',a:'moveabs',fx:Math.max(0,Math.min(1,f2.x)),
        fy:Math.max(0,Math.min(1,f2.y))});
  }else{
   if(!G.down&&G.moved>16&&(Date.now()-G.t0)>260){
     G.down=true;G.mode='drag';cmd({t:'mouse',a:'down'});
   }else if(G.moved>4){
     cmd({t:'mouse',a:'move',dx:Math.round(dx*2.2),dy:Math.round(dy*2.2)});
   }
  }
  G.px=t.clientX;G.py=t.clientY;
 }
},{passive:false});
stage.addEventListener('touchend',function(e){
 e.preventDefault();
 clearLong();
 if(G.mode==='pinch'){
  if(vS<1.05){fitView();}else{clampView();apply();}
  if(e.touches.length===0){G=newState('idle');}
  return;
 }
 if(G.mode==='one'){
  if(G.rc){G=newState('idle');return;}
  if(G.moved<=14&&vS<=1.01){
   var f=frac(G.x0,G.y0),now=Date.now();
   var fx=Math.max(0,Math.min(1,f.x)),fy=Math.max(0,Math.min(1,f.y));
   if(now-lastTap<300){
     cmd({t:'mouse',a:'dtap',fx:fx,fy:fy});lastTap=0;
   }else{
     cmd({t:'mouse',a:'tap',fx:fx,fy:fy});lastTap=now;
   }
  }
 }else if(G.mode==='drag'){
  cmd({t:'mouse',a:'up'});
 }
 G=newState('idle');
},{passive:false});
window.addEventListener('resize',function(){clampView();apply();});
document.getElementById('fit').onclick=function(){
 if(vS>1.01){fitView();}else{vS=2;vX=0;vY=0;clampView();apply();}
};


document.getElementById('fab').onclick=function(){
 var d=document.getElementById('drawer');
 d.style.display=(d.style.display==='block')?'none':'block';
};
function kb(id,body){document.getElementById(id).onclick=function(){cmd(body)};}
kb('k_enter',{t:'key',a:'press',k:'enter'});
kb('k_esc',{t:'key',a:'press',k:'esc'});
kb('k_tab',{t:'key',a:'press',k:'tab'});
kb('k_bs',{t:'key',a:'press',k:'backspace'});
kb('k_copy',{t:'key',a:'hotkey',k:['ctrl','c']});
kb('k_paste',{t:'key',a:'hotkey',k:['ctrl','v']});
kb('k_altab',{t:'key',a:'hotkey',k:['alt','tab']});
kb('k_win',{t:'key',a:'press',k:'win'});
kb('k_winl',{t:'key',a:'hotkey',k:['win','l']});
kb('k_up',{t:'key',a:'press',k:'pageup'});
kb('k_dn',{t:'key',a:'press',k:'pagedown'});
kb('k_volup',{t:'key',a:'press',k:'volumeup'});
kb('k_voldn',{t:'key',a:'press',k:'volumedown'});
kb('k_mute',{t:'key',a:'press',k:'volumemute'});
kb('k_play',{t:'key',a:'press',k:'playpause'});
document.getElementById('k_send').onclick=function(){
 var v=document.getElementById('txt').value;
 if(v){cmd({t:'type',text:v});}
 document.getElementById('txt').value='';
};
var ap=['notepad','calc','chrome','explorer','taskmgr','cmd','paint'];
for(var j=0;j<ap.length;j++){(function(n){
 var b=document.createElement('button');b.textContent=n;
 b.onclick=function(){cmd({t:'app',name:n})};
 document.getElementById('apps').appendChild(b)})(ap[j])}
document.getElementById('ls').onclick=function(){
 cmd({t:'files',path:document.getElementById('fpath').value});};
document.getElementById('home').onclick=function(){
 document.getElementById('fpath').value='';cmd({t:'files',path:''});};
document.getElementById('shut').onclick=function(){
 if(confirm('PC ochirilsinmi?')){cmd({t:'power',a:'shutdown'})}};
document.getElementById('reb').onclick=function(){
 if(confirm('Qayta yuklansinmi?')){cmd({t:'power',a:'reboot'})}};
function showFiles(d){
 var f=document.getElementById('files');
 f.innerHTML='<b>'+d.path+'</b>';
 (d.items||[]).forEach(function(it){
  var el=document.createElement('div');
  el.textContent=(it.dir?'[PAPKA] ':'[FAYL] ')+it.name;
  el.onclick=function(){
   if(it.dir){document.getElementById('fpath').value=it.full;cmd({t:'files',path:it.full});}
   else{cmd({t:'open',path:it.full});}};
  f.appendChild(el);});}
</script></body></html>"""


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass
    def js(self, o, code=200, extra=None):
        try:
            b = json.dumps(o).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(b)))
            self.send_header("Cache-Control", "no-store")
            if extra:
                for k, v in extra.items():
                    self.send_header(k, v)
            self.end_headers()
            self.wfile.write(b)
        except (BrokenPipeError, ConnectionResetError):
            pass
    def rd(self):
        try:
            n = int(self.headers.get("Content-Length", 0))
            return json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            return {}
    def chk(self, d):
        return d.get("code") == PAIR_CODE
    def do_GET(self):
        try:
            u = urlparse(self.path)
            if u.path == "/":
                b = (P1 + P2).encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(b)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(b)
                return
            q = parse_qs(u.query)
            if (q.get("code") or [""])[0] != PAIR_CODE:
                self.js({"err": "bad code"}, 403)
                return
            if u.path == "/poll":
                who = (q.get("who") or [""])[0]
                since = int((q.get("since") or ["0"])[0])
                end = time.time() + 20
                while True:
                    if any(m["id"] > since for m in inbox.get(who, [])):
                        break
                    if time.time() > end:
                        break
                    time.sleep(0.25)
                msgs = [m for m in inbox.get(who, []) if m["id"] > since]
                self.js({"msgs": msgs})
                return
            if u.path == "/img":
                if not latest_img["data"]:
                    self.js({"err": "no img yet"}, 404)
                    return
                want = (q.get("v") or ["-1"])[0]
                if want.isdigit() and int(want) == latest_img["v"]:
                    self.send_response(304)
                    self.send_header("X-Version", str(latest_img["v"]))
                    self.end_headers()
                    return
                data = latest_img["data"]
                self.send_response(200)
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Content-Length", str(len(data)))
                self.send_header("X-Version", str(latest_img["v"]))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(data)
                return
            if u.path == "/status":
                age = time.time() - agent_ts["t"] if agent_ts["t"] else 9999
                self.js({"agent_age": round(age, 1), "v": latest_img["v"],
                         "hub": len(inbox.get("pc", [])),
                         "hup": len(inbox.get("phone", []))})
                return
            self.js({}, 404)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            pass
    def do_POST(self):
        try:
            d = self.rd()
            if not self.chk(d):
                self.js({"err": "bad code"}, 403)
                return
            if self.path == "/send":
                to = d.get("to", "pc")
                q = inbox.setdefault(to, [])
                mid = seen.get(to, 0) + 1
                seen[to] = mid
                q.append({"id": mid, "ts": time.time(),
                          "from": d.get("from", "?"), "cmd": d.get("cmd", {})})
                while len(q) > MAXQ:
                    q.pop(0)
                self.js({"id": mid})
                return
            if self.path == "/push":
                try:
                    raw = base64.b64decode(d.get("img", ""))
                    if raw:
                        latest_img["data"] = raw
                        latest_img["v"] += 1
                except Exception:
                    pass
                agent_ts["t"] = time.time()
                self.js({"v": latest_img["v"]})
                return
            if self.path == "/hb":
                agent_ts["t"] = time.time()
                self.js({"ok": True})
                return
            if self.path == "/ack":
                who = d.get("who", "pc")
                upto = int(d.get("upto", 0))
                inbox[who] = [m for m in inbox.get(who, []) if m["id"] > upto]
                self.js({"ok": True})
                return
            self.js({}, 404)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            pass

if __name__ == "__main__":
    lip = lan_ip()
    print("=" * 55, flush=True)
    print("  RELAY SERVER v3 ISHGA TUSHDI!", flush=True)
    print("=" * 55, flush=True)
    print("PORT:      %d" % PORT, flush=True)
    print("KOD (PIN): %s" % PAIR_CODE, flush=True)
    print("-" * 55, flush=True)
    print("Telefondan brauzerda oching (Wi-Fi bir xil bo'lsa):", flush=True)
    print("  --> http://%s:%d" % (lip, PORT), flush=True)
    print("-" * 55, flush=True)
    print("Agent sozlamasi (agent_settings.json):", flush=True)
    print('  "RELAY": "http://127.0.0.1:%d"' % PORT, flush=True)
    print('  "CODE":  "%s"' % PAIR_CODE, flush=True)
    print("=" * 55, flush=True)
    try:
        ThreadingHTTPServer(("0.0.0.0", PORT), H).serve_forever()
    except KeyboardInterrupt:
        print("\nTo'xtatildi.", flush=True)


