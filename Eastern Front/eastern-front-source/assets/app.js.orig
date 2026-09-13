(()=>{
'use strict';
const D=HISTORY, T=THREE, root=document.getElementById('ef-app');
const stage=document.getElementById('stage'), labels=document.getElementById('labels'), canvas=document.getElementById('scene');
const black=0x111318,red=0xc92535;
const renderer=new T.WebGLRenderer({canvas,antialias:true,alpha:true,preserveDrawingBuffer:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));renderer.setClearColor(0xeeeae1,0);renderer.outputColorSpace=T.SRGBColorSpace;
const scene=new T.Scene(),camera=new T.PerspectiveCamera(39,1,.1,300);
scene.add(new T.HemisphereLight(0xffffff,0x7c827b,2.6));const sun=new T.DirectionalLight(0xffffff,2.6);sun.position.set(-20,40,25);scene.add(sun);
const world=new T.Group();scene.add(world);
const CW=2048, scale=CW/(40*Math.PI/180), merc=lat=>Math.log(Math.tan(Math.PI/4+lat*Math.PI/360));
const CH=Math.round(scale*(merc(61.7)-merc(42))), MW=38,MH=CH/CW*MW;
const projection=d3.geoMercator().scale(scale).translate([-scale*10*Math.PI/180,scale*merc(61.7)]).clipExtent([[0,0],[CW,CH]]);
const land=topojson.feature(LAND,LAND.objects.land), geoPath=d3.geoPath(projection);
const ll=p=>{const q=projection(p);return new T.Vector3(q[0]/CW*MW-MW/2,.08,q[1]/CH*MH-MH/2)};
const map=document.createElement('canvas');map.width=CW;map.height=CH;const mc=map.getContext('2d');
const landPath=new Path2D(geoPath(land));
mc.fillStyle='#bdd4d8';mc.fillRect(0,0,CW,CH);mc.fillStyle='#e6e2d3';mc.fill(landPath);mc.strokeStyle='#98aa9e';mc.lineWidth=1.6;mc.stroke(landPath);
mc.save();mc.clip(landPath);mc.strokeStyle='rgba(87,106,95,.16)';mc.lineWidth=1;
for(let lon=10;lon<=50;lon+=5){mc.beginPath();geoPath.context(mc)({type:'LineString',coordinates:[[lon,42],[lon,61.7]]});mc.stroke()}
for(let lat=45;lat<=60;lat+=5){mc.beginPath();geoPath.context(mc)({type:'LineString',coordinates:[[10,lat],[50,lat]]});mc.stroke()}
mc.restore();mc.beginPath();geoPath.context(mc)(RIVERS);mc.strokeStyle='#8cb5bb';mc.lineWidth=2.4;mc.stroke();geoPath.context(null);
// The base depicts coastlines, with no modern political borders or invented terrain elevation.
const texture=new T.CanvasTexture(map);texture.colorSpace=T.SRGBColorSpace;texture.anisotropy=4;
const plate=new T.Mesh(new T.BoxGeometry(MW,.65,MH),new T.MeshStandardMaterial({color:0x81989a,roughness:1}));plate.position.y=-.36;world.add(plate);
const top=new T.Mesh(new T.PlaneGeometry(MW,MH),new T.MeshStandardMaterial({map:texture,roughness:1}));top.rotation.x=-Math.PI/2;top.position.y=.005;world.add(top);
const ground=new T.Mesh(new T.PlaneGeometry(140,100),new T.MeshBasicMaterial({color:0xeeeae1}));ground.rotation.x=-Math.PI/2;ground.position.y=-.76;world.add(ground);
const dynCanvas=document.createElement('canvas');dynCanvas.width=CW;dynCanvas.height=CH;const dc=dynCanvas.getContext('2d');
const dt=new T.CanvasTexture(dynCanvas);dt.colorSpace=T.SRGBColorSpace;const overlay=new T.Mesh(new T.PlaneGeometry(MW,MH),new T.MeshBasicMaterial({map:dt,transparent:true,depthWrite:false}));overlay.rotation.x=-Math.PI/2;overlay.position.y=.04;world.add(overlay);
const matDe=new T.MeshStandardMaterial({color:black,roughness:.68}),matSu=new T.MeshStandardMaterial({color:red,roughness:.65});
const sideDe=new T.MeshStandardMaterial({color:0x40444b,roughness:1}),sideSu=new T.MeshStandardMaterial({color:0x841e29,roughness:1});
function tank(mat,track){const g=new T.Group();const box=(x,y,z,a,b,c,m)=>{const o=new T.Mesh(new T.BoxGeometry(a,b,c),m);o.position.set(x,y,z);g.add(o)};box(0,.13,0,.63,.22,.39,mat);box(0,.075,-.25,.7,.16,.13,track);box(0,.075,.25,.7,.16,.13,track);box(-.04,.31,0,.30,.16,.26,mat);box(.29,.34,0,.44,.055,.055,mat);return g}
const troops=[];for(let i=0;i<22;i++){for(const side of ['de','su']){const obj=tank(side==='de'?matDe:matSu,side==='de'?sideDe:sideSu);world.add(obj);troops.push({obj,side,i})}}
let currentSec=0,playing=true,speed=1,azimuth=-.1,elevation=.91,zoom=1,autoCamera=true,lastIndex=-1,lastStamp=-1;
let total=0;D.keyframes.forEach(k=>{k.t=total;total+=k.seconds;k.ms=Date.parse(k.date+'T00:00:00Z');k.p=k.line.map(ll)});const endT=D.keyframes.at(-1).t;
function resample(points,n){const len=[0];for(let i=1;i<points.length;i++)len[i]=len[i-1]+points[i].distanceTo(points[i-1]);let ix=1;return Array.from({length:n},(_,i)=>{const v=i/(n-1)*len.at(-1);while(ix<len.length-1&&len[ix]<v)ix++;return points[ix-1].clone().lerp(points[ix],(v-len[ix-1])/(len[ix]-len[ix-1]||1))})}
D.keyframes.forEach(k=>k.samples=resample(k.p,110));
function state(sec){let i=D.keyframes.findLastIndex(k=>k.t<=sec);i=Math.max(0,i);const a=D.keyframes[i],b=D.keyframes[Math.min(i+1,D.keyframes.length-1)],u=b.t===a.t?0:Math.min(1,(sec-a.t)/(b.t-a.t));return {i,a,b,u,ms:a.ms+(b.ms-a.ms)*u,front:a.samples.map((v,j)=>v.clone().lerp(b.samples[j],u))}}
function timeOf(date){const ms=Date.parse(date+'T00:00:00Z');for(let i=0;i<D.keyframes.length-1;i++){const a=D.keyframes[i],b=D.keyframes[i+1];if(ms>=a.ms&&ms<=b.ms)return a.t+(ms-a.ms)/(b.ms-a.ms)*(b.t-a.t)}return ms<D.keyframes[0].ms?0:endT}
function addLine(pts,color,radius=.025){const curve=new T.CatmullRomCurve3(pts);return new T.Mesh(new T.TubeGeometry(curve,Math.max(20,pts.length*2),radius,5,false),new T.MeshStandardMaterial({color,roughness:.75}))}
const arrows=D.arrows.map(a=>{const p=a.pts.map(ll);p.forEach((v,i)=>v.y=.2+(i===1?.55:0));const curve=new T.CatmullRomCurve3(p),g=new T.Group(),color=a.side==='de'?black:red;world.add(g);const tube=new T.Mesh(new T.TubeGeometry(curve,60,.09,6,false),new T.MeshStandardMaterial({color,roughness:.7}));g.add(tube);const head=new T.Mesh(new T.ConeGeometry(.30,.68,4),a.side==='de'?matDe:matSu);g.add(head);const mover=tank(a.side==='de'?matDe:matSu,a.side==='de'?sideDe:sideSu);g.add(mover);return {...a,curve,g,tube,head,mover,startT:timeOf(a.start),endT:timeOf(a.end)}});
const cityLabels=D.cities.map((c,i)=>{const p=ll(c.slice(1));const pin=new T.Mesh(new T.CylinderGeometry(.075,.075,.15,10),new T.MeshStandardMaterial({color:0x555b58}));pin.position.copy(p);pin.position.y=.12;world.add(pin);const el=document.createElement('span');el.className='city';el.textContent=c[0];labels.append(el);return {el,p,name:c[0],i}});
const seaLabels=[['バルト海',[19,57.3]],['黒海',[32,43.8]],['コーカサス',[43.4,42.6]]].map(([name,p])=>{const el=document.createElement('span');el.className='sea';el.textContent=name;labels.append(el);return {el,p:ll(p)}});
const pocketG=new T.Group();world.add(pocketG);
const pockets=[{name:'第6軍などの包囲',at:[44.2,48.75],start:'1942-11-23',end:'1943-02-02',rx:.44,rz:.34},{name:'クールラント',at:[22.1,56.9],start:'1944-10-10',end:'1945-05-09',rx:.73,rz:.50},{name:'東プロイセン',at:[20.3,54.5],start:'1945-02-01',end:'1945-04-25',rx:.55,rz:.35}].map(p=>{const pos=ll(p.at),pts=Array.from({length:65},(_,i)=>new T.Vector3(pos.x+Math.cos(i/64*Math.PI*2)*p.rx,.18,pos.z+Math.sin(i/64*Math.PI*2)*p.rz));const ring=addLine(pts,red,.038);pocketG.add(ring);const unit=tank(matDe,sideDe);unit.scale.setScalar(.7);unit.position.copy(pos);pocketG.add(unit);const el=document.createElement('span');el.className='pocket';el.textContent=p.name;labels.append(el);return {...p,pos,ring,unit,el,startT:timeOf(p.start),endT:timeOf(p.end)}});
const focusRing=new T.Mesh(new T.RingGeometry(.6,.65,64),new T.MeshBasicMaterial({color:0x9e743d,transparent:true,opacity:.7,side:T.DoubleSide}));focusRing.rotation.x=-Math.PI/2;world.add(focusRing);
const compass=document.createElement('div');compass.className='compass';compass.innerHTML='<span>北 N</span><b>↑</b>';stage.append(compass);
function drawRibbon(front,s){dc.clearRect(0,0,CW,CH);dc.save();dc.clip(landPath);
const toPix=v=>[(v.x/MW+.5)*CW,(v.z/MH+.5)*CH];const offset=(pts,dir,width)=>pts.map((p,i)=>{const q=pts[Math.min(i+1,pts.length-1)].clone().sub(pts[Math.max(i-1,0)]);const n=new T.Vector3(q.z,0,-q.x).normalize().multiplyScalar(width*dir);return p.clone().add(n)});
for(const [side,dir,color] of [['de',-1,'rgba(17,19,24,.19)'],['su',1,'rgba(201,37,53,.16)']]){const edge=offset(front,dir,.65);dc.beginPath();front.forEach((p,i)=>{const q=toPix(p);i?dc.lineTo(...q):dc.moveTo(...q)});edge.reverse().forEach(p=>dc.lineTo(...toPix(p)));dc.closePath();dc.fillStyle=color;dc.fill()}
const stroke=(pts,color,width)=>{dc.beginPath();pts.forEach((p,i)=>{const q=toPix(p);i?dc.lineTo(...q):dc.moveTo(...q)});dc.strokeStyle=color;dc.lineWidth=width;dc.lineJoin='round';dc.lineCap='round';dc.stroke()};
stroke(front,'rgba(255,255,255,.9)',6);stroke(offset(front,-1,.05),'#111318',2.9);stroke(offset(front,1,.05),'#c92535',2.9);
// Faint invasion start line is a reference front, not a political boundary.
dc.setLineDash([8,10]);stroke(D.keyframes[0].samples,'rgba(87,83,73,.38)',1.5);dc.restore();dt.needsUpdate=true;
return offset;
}
function placeLabel(el,p,dy=0){const q=p.clone();q.y=.35;world.localToWorld(q);q.project(camera);const w=stage.clientWidth,h=stage.clientHeight;el.style.left=((q.x*.5+.5)*w)+'px';el.style.top=((-q.y*.5+.5)*h+dy)+'px';el.style.visibility=q.z>1||q.x<-1||q.x>1||q.y<-1||q.y>1?'hidden':'visible'}
function frame(sec){currentSec=Math.min(total,Math.max(0,sec));const s=state(currentSec),f=s.front;
if(autoCamera){azimuth=-.09+.10*Math.sin(currentSec/total*Math.PI*2);elevation=.97+.045*Math.sin(currentSec/total*Math.PI*2);}
const dist=48/zoom*Math.max(1,1.7/camera.aspect);camera.position.set(Math.sin(azimuth)*Math.cos(elevation)*dist,Math.sin(elevation)*dist,Math.cos(azimuth)*Math.cos(elevation)*dist);camera.lookAt(0,0,0);camera.updateMatrixWorld();
const off=drawRibbon(f,s);
const german=off(f,-1,.43),soviet=off(f,1,.43);
for(const tr of troops){const j=Math.round((tr.i+0.5)/22*(f.length-1)),p=(tr.side==='de'?german:soviet)[j];tr.obj.position.copy(p);tr.obj.position.y=.07;
const q=f[Math.min(j+1,f.length-1)].clone().sub(f[Math.max(0,j-1)]);const n=new T.Vector3(q.z,0,-q.x).normalize().multiplyScalar(tr.side==='de'?1:-1);tr.obj.rotation.y=-Math.atan2(n.z,n.x);
const px=(p.x/MW+.5)*CW,py=(p.z/MH+.5)*CH;tr.obj.visible=currentSec<endT&&mc.isPointInPath(landPath,px,py);}
for(const a of arrows){const dur=a.endT-a.startT,t=(currentSec-a.startT)/dur;a.g.visible=t>=0&&t<=1&&currentSec<endT;if(!a.g.visible)continue;const u=Math.max(.035,Math.min(.995,t));const count=Math.floor(60*u)*6*6;a.tube.geometry.setDrawRange(0,count);const p=a.curve.getPoint(u),dir=a.curve.getTangent(u).normalize();a.head.position.copy(p);a.head.quaternion.setFromUnitVectors(new T.Vector3(0,1,0),dir);const m=a.curve.getPoint(Math.max(0,u-.09));a.mover.position.copy(m);a.mover.position.y=.1;a.mover.rotation.y=-Math.atan2(dir.z,dir.x);}
for(const p of pockets){const on=currentSec>=p.startT&&currentSec<p.endT;p.ring.visible=p.unit.visible=on;p.el.style.display=on?'block':'none';if(on){p.ring.scale.y=1;placeLabel(p.el,p.pos,24)}}
const focus=s.a.focus;focusRing.position.copy(ll(focus));focusRing.position.y=.11;focusRing.scale.setScalar(1+.08*Math.sin(currentSec*2));focusRing.visible=currentSec<endT;
renderer.render(scene,camera);
const large=stage.clientWidth>800;cityLabels.forEach(c=>{c.el.style.display=!large&&![0,4,5,6,7,9].includes(c.i)?'none':'block';c.el.classList.toggle('highlight',Math.hypot(c.p.x-focusRing.position.x,c.p.z-focusRing.position.z)<2.5);placeLabel(c.el,c.p,-18)});seaLabels.forEach(c=>placeLabel(c.el,c.p));
compass.style.transform='rotate('+(-azimuth*180/Math.PI)+'deg)';
const date=new Date(s.ms);const text=date.toISOString().slice(0,10).replaceAll('-',' / ');document.getElementById('date').textContent=text;
if(lastIndex!==s.i){document.getElementById('chapter').textContent=String(s.i+1).padStart(2,'0')+' / '+D.keyframes.length;document.getElementById('event').textContent=s.a.title;document.getElementById('note').textContent=s.a.note;document.getElementById('chapters').value=s.i;lastIndex=s.i}
document.getElementById('seek').value=currentSec;document.getElementById('time').textContent=Math.floor(currentSec/60)+':'+String(Math.floor(currentSec%60)).padStart(2,'0')+' / '+Math.floor(total/60)+':'+String(total%60).padStart(2,'0');
const rawDate=date.toISOString().slice(0,10);const event=D.events.findLast(e=>e.date<=rawDate);document.getElementById('event').textContent=event.title;document.getElementById('note').textContent=event.note;if(rawDate>='1942-11-19'&&rawDate<'1942-11-23'){document.getElementById('event').textContent='ウラヌス作戦：南北から包囲';document.getElementById('note').textContent='ソ連軍が突出部の側面を突破。スターリングラード西方での合流を目指す。';}
document.getElementById('end').style.opacity=currentSec>=endT?Math.min(1,(currentSec-endT)/1.5):0;
}
function resize(){renderer.setSize(stage.clientWidth,stage.clientHeight,false);camera.aspect=stage.clientWidth/stage.clientHeight;camera.updateProjectionMatrix();frame(currentSec)}
const seek=document.getElementById('seek');seek.max=total;seek.addEventListener('input',()=>{playing=false;syncPlay();frame(+seek.value)});
const select=document.getElementById('chapters');D.keyframes.forEach((k,i)=>{const o=document.createElement('option');o.value=i;o.textContent=k.date+'　'+k.title;select.add(o)});select.onchange=()=>{playing=false;syncPlay();frame(D.keyframes[+select.value].t)};
function syncPlay(){document.getElementById('play').textContent=playing?'一時停止':'再生';document.getElementById('play').setAttribute('aria-pressed',String(playing))}
document.getElementById('play').onclick=()=>{if(currentSec>=total)currentSec=0;playing=!playing;syncPlay()};document.getElementById('restart').onclick=()=>{currentSec=0;playing=true;syncPlay();frame(0)};
document.getElementById('speed').onchange=e=>speed=+e.target.value;
document.getElementById('view').onclick=()=>{autoCamera=!autoCamera;azimuth=0;elevation=autoCamera?.97:1.55;zoom=1;document.getElementById('view').textContent=autoCamera?'真上から見る':'斜めから見る';frame(currentSec)};
let drag=null;canvas.onpointerdown=e=>{drag={x:e.clientX,y:e.clientY,az:azimuth,el:elevation};autoCamera=false;canvas.setPointerCapture(e.pointerId)};canvas.onpointermove=e=>{if(!drag)return;azimuth=drag.az-(e.clientX-drag.x)*.004;elevation=Math.max(.48,Math.min(1.55,drag.el+(e.clientY-drag.y)*.004));frame(currentSec)};canvas.onpointerup=()=>drag=null;
canvas.addEventListener('wheel',e=>{e.preventDefault();zoom=Math.max(.75,Math.min(1.6,zoom-e.deltaY*.0006));frame(currentSec)},{passive:false});
canvas.addEventListener('keydown',e=>{if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key)){e.preventDefault();autoCamera=false;azimuth+=(e.key==='ArrowLeft'?.08:e.key==='ArrowRight'?-.08:0);elevation=Math.max(.48,Math.min(1.55,elevation+(e.key==='ArrowUp'?.05:e.key==='ArrowDown'?-.05:0)));frame(currentSec)}});
D.sources.forEach(s=>{const a=document.createElement('a');a.href=s.url;a.textContent=s.title;a.target='_blank';a.rel='noopener';document.getElementById('sources').append(a)});
window.animation={seek:sec=>{playing=false;syncPlay();frame(sec)},duration:total,state:()=>({time:currentSec,date:document.getElementById('date').textContent,chapter:document.getElementById('event').textContent,tanks:troops.filter(t=>t.obj.visible).length}),ready:true};
new ResizeObserver(resize).observe(stage);resize();syncPlay();let prev=performance.now();function animate(now){const dt=Math.min(.05,(now-prev)/1000);prev=now;if(playing){currentSec+=dt*speed;if(currentSec>=total){currentSec=total;playing=false;syncPlay()}frame(currentSec)}requestAnimationFrame(animate)}requestAnimationFrame(animate);
})();
