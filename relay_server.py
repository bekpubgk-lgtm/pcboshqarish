"""Relay v2 - brauzer UI bilan. PC agent + telefon brauzeri shu yerga ulanadi."""
import json, time, base64, os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
PORT = int(os.environ.get("PORT", "8888"))
PAIR_CODE = os.environ.get("PAIR_CODE", "PC-2026-77AA")
MAXQ = 200
inbox = {}
seen = {}
latest_img = {"data": b"", "ts": 0}
P1 = """<!DOCTYPE html><html><head><meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no'>
<title>PC Remote</title><style>
body{margin:0;background:#111;color:#eee;font-family:sans-serif}
#lock{position:fixed;inset:0;background:#111;display:flex;flex-direction:column;gap:10px;align-items:center;justify-content:center;z-index:9}
#lock input{padding:12px;font-size:18px;border-radius:10px;border:0;width:220px;text-align:center}
#scr{width:100%;display:block;background:#000;touch-action:none}
#pad{height:130px;background:#1c1c1c;border:2px solid #333;border-radius:12px;margin:8px;touch-action:none;text-align:center;color:#777;padding-top:50px}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;padding:0 8px}
button{background:#2d2d2d;color:#fff;border:0;border-radius:10px;padding:13px 0;font-size:15px}
button:active{background:#666}.row{display:flex;gap:6px;padding:6px 8px}
.row button{flex:1}.row input{flex:3;border-radius:10px;border:0;padding:12px}
.bar{display:flex;gap:6px;padding:6px 8px;align-items:center}
.bar input{flex:1;padding:10px;border-radius:8px;border:0}
.st{font-size:12px;color:#8f8;padding:0 8px}
#files{padding:0 8px 20px}#files div{padding:10px;background:#1c1c1c;margin:4px 0;border-radius:8px}
</style></head><body>
<div id='lock'><h2>PC Remote</h2>
<input id='srv' placeholder='http://server:8888'>
<input id='pin' type='password' placeholder='Kod'>
<button onclick='login()'>Kirish</button></div>
<h3 style='text-align:center'>PC Remote <span id='fps' style='font-size:11px;color:#8f8'></span></h3>
<div class='bar'><input id='srv2' placeholder='server'><input id='pin2' placeholder='kod' style='max-width:130px'></div>
<div class='st' id='st'>ulanmagan</div>
<img id='scr'>
<div id='pad'>Touchpad - suring, 1 bossa=klik, tez 2 bossa=2x</div>
<div class='grid'>
<button id='lc'>Sol klik</button><button id='rc'>Ong klik</button><button id='dc'>2x</button><button id='enter'>Enter</button>
<button id='esc'>Esc</button><button id='altab'>Alt+Tab</button><button id='copy'>Copy</button><button id='paste'>Paste</button>
<button id='volm'>Vol-</button><button id='volp'>Vol+</button><button id='mute'>Mute</button><button id='winl'>Win+L</button>
</div>
<div class='row'><input id='txt' placeholder='Matn...'><button id='send'>Yuborish</button></div>
<div class='grid' id='apps'></div>
<div class='row'><input id='fpath' placeholder='papka (bosh=uy papkasi)'><button id='ls'>Fayllar</button></div>
<div id='files'></div>
<div class='row'><button id='shut'>Ochirish</button><button id='reb'>Qayta</button><button id='ref'>Ekran</button></div>
<script>
var SRV='',CODE='';
"""
P2 = """function st(t){document.getElementById('st').textContent=t}
function req(path,body,ms){
 ms=ms||15000;
 var url=(path.charAt(0)==='/'&&(SRV===''||SRV===window.location.origin))?path:(SRV+path);
 return new Promise(function(resolve,reject){
  var done=false;
  var timer=setTimeout(function(){
   if(!done){done=true;reject(new Error('timeout'));}},ms);
  fetch(url,{method:body?'POST':'GET',
   headers:{'Content-Type':'application/json'},
   body:body?JSON.stringify(body):undefined})
  .then(function(r){if(!done){done=true;clearTimeout(timer);resolve(r);}})
  .catch(function(e){if(!done){done=true;clearTimeout(timer);reject(e);}});
 });}
var pid=0;
function cmd(c){
 req('/send',{code:CODE,from:'phone',to:'pc',cmd:c},10000).catch(function(e){st('xato: '+e)});
}
function poll(){
 req('/poll?code='+encodeURIComponent(CODE)+'&who=phone&since='+pid, null, 20000)
 .then(function(r){return r.json()}).then(function(d){
  var mx=pid;
  (d.msgs||[]).forEach(function(m){mx=Math.max(mx,m.id);
   if(m.cmd&&m.cmd.t==='files_res'){showFiles(m.cmd);}});
  if(mx>pid){req('/ack',{code:CODE,who:'phone',upto:mx},8000).catch(function(){}) ; pid=mx;}
  poll();
 }).catch(function(){setTimeout(poll,2000)});
}
function login(){
 var s=(document.getElementById('srv').value||document.getElementById('srv2').value||'').trim();
 if(s){SRV=s;if(SRV.slice(-1)==='/'){SRV=SRV.slice(0,-1);}}else{SRV=window.location.origin;}
 CODE=(document.getElementById('pin').value||document.getElementById('pin2').value||'').trim();
 if(!CODE){alert('Kodni kiriting');return;}
 document.getElementById('srv2').value=SRV;document.getElementById('pin2').value=CODE;
 req('/send',{code:CODE,from:'phone',to:'pc',cmd:{t:'ping'}},10000)
 .then(function(r){if(!r.ok){throw new Error('kod xato');}return r.json();}).then(function(){
  document.getElementById('lock').style.display='none';
  st('ulandi: '+SRV);poll();shot();
 }).catch(function(e){alert('Ulanmadi: '+e.message)});
}
function move(dx,dy){cmd({t:'mouse',a:'move',dx:Math.round(dx*3),dy:Math.round(dy*3)})}
var lx=0,ly=0,lastTap=0;
var pad=document.getElementById('pad');
pad.addEventListener('touchstart',function(e){lx=e.touches[0].clientX;ly=e.touches[0].clientY},{passive:true});
pad.addEventListener('touchmove',function(e){var t=e.touches[0];move(t.clientX-lx,t.clientY-ly);lx=t.clientX;ly=t.clientY;e.preventDefault()},{passive:false});
pad.addEventListener('touchend',function(){
 var n=Date.now();
 if(n-lastTap<300){cmd({t:'mouse',a:'dclick'})}
 else{var tt=n;setTimeout(function(){if(lastTap===tt)cmd({t:'mouse',a:'click'})},320)}
 lastTap=n;});
var scr=document.getElementById('scr');
scr.addEventListener('touchstart',function(e){
 var r=scr.getBoundingClientRect();
 var t=e.touches[0];
 var x=(t.clientX-r.left)/r.width, y=(t.clientY-r.top)/r.height;
 cmd({t:'mouse',a:'tap',fx:x,fy:y});
},{passive:true});
function btn(id,body){document.getElementById(id).onclick=function(){cmd(body)}}
btn('lc',{t:'mouse',a:'click',b:'left'});btn('rc',{t:'mouse',a:'click',b:'right'});
btn('dc',{t:'mouse',a:'dclick'});btn('enter',{t:'key',a:'press',k:'enter'});
btn('esc',{t:'key',a:'press',k:'esc'});
btn('altab',{t:'key',a:'hotkey',k:['alt','tab']});
btn('copy',{t:'key',a:'hotkey',k:['ctrl','c']});
btn('paste',{t:'key',a:'hotkey',k:['ctrl','v']});
btn('volm',{t:'key',a:'press',k:'volumedown'});
btn('volp',{t:'key',a:'press',k:'volumeup'});
btn('mute',{t:'key',a:'press',k:'volumemute'});
btn('winl',{t:'key',a:'hotkey',k:['win','l']});
document.getElementById('send').onclick=function(){
 var v=document.getElementById('txt').value;
 cmd({t:'type',text:v});document.getElementById('txt').value='';};
var ap=['notepad','calc','chrome','explorer','taskmgr','cmd','paint'];
for(var j=0;j<ap.length;j++){(function(n){
 var b=document.createElement('button');b.textContent=n;
 b.onclick=function(){cmd({t:'app',name:n})};
 document.getElementById('apps').appendChild(b)})(ap[j])}
document.getElementById('shut').onclick=function(){
 if(confirm('Ochirilsinmi?'))cmd({t:'power',a:'shutdown'})};
document.getElementById('reb').onclick=function(){
 if(confirm('Qayta yuklansinmi?'))cmd({t:'power',a:'reboot'})};
document.getElementById('ref').onclick=function(){shot()};
var fps=0,lastF=Date.now();
function shot(){
 req('/img?code='+encodeURIComponent(CODE),null,15000).then(function(r){return r.blob()})
 .then(function(b){
  document.getElementById('scr').src=URL.createObjectURL(b);
  fps++;var n=Date.now();
  if(n-lastF>2000){document.getElementById('fps').textContent=Math.round(fps*1000/(n-lastF))+' fps';fps=0;lastF=n;}
  setTimeout(shot,600);
 }).catch(function(){setTimeout(shot,2000)});
}
function showFiles(d){
 var f=document.getElementById('files');f.innerHTML='<b>'+d.path+'</b>';
 (d.items||[]).forEach(function(it){
  var el=document.createElement('div');
  el.textContent=(it.dir?'D ':'F ')+it.name;
  el.onclick=function(){
   if(it.dir){document.getElementById('fpath').value=it.full;cmd({t:'files',path:it.full});}
   else{cmd({t:'open',path:it.full});}};
  f.appendChild(el);});}
document.getElementById('ls').onclick=function(){
 cmd({t:'files',path:document.getElementById('fpath').value});};
</script></body></html>"""

class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass
    def js(self, o, code=200):
        try:
            b = json.dumps(o).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(b)))
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
                msgs = [m for m in inbox.get(who, []) if m["id"] > since]
                self.js({"msgs": msgs})
                return
            if u.path == "/img":
                if not latest_img["data"]:
                    self.js({"err": "no img yet"}, 404)
                    return
                self.send_response(200)
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Content-Length", str(len(latest_img["data"])))
                self.end_headers()
                self.wfile.write(latest_img["data"])
                return
            self.js({}, 404)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            pass
    def do_POST(self):
        d = self.rd()
        if not self.chk(d):
            self.js({"err": "bad code"}, 403)
            return
        if self.path == "/send":
            to = d.get("to", "pc")
            q = inbox.setdefault(to, [])
            mid = seen.get(to, 0) + 1
            seen[to] = mid
            q.append({"id": mid, "ts": time.time(), "from": d.get("from", "?"),
                      "cmd": d.get("cmd", {})})
            while len(q) > MAXQ:
                q.pop(0)
            self.js({"id": mid})
            return
        if self.path == "/push":
            try:
                latest_img["data"] = base64.b64decode(d.get("img", ""))
                latest_img["ts"] = time.time()
            except Exception:
                pass
            self.js({"ok": True})
            return
        if self.path == "/ack":
            who = d.get("who", "pc")
            upto = int(d.get("upto", 0))
            inbox[who] = [m for m in inbox.get(who, []) if m["id"] > upto]
            self.js({"ok": True})
            return
        self.js({}, 404)
if __name__ == "__main__":
    print("Relay v2: http://0.0.0.0:%d" % PORT, flush=True)
    print("CODE: %s" % PAIR_CODE, flush=True)
    print("Brauzer: http://SERVER_IP:%d" % PORT, flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), H).serve_forever()

