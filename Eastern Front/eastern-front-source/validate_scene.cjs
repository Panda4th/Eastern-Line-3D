const fs=require('fs'),vm=require('vm'),assert=require('assert');
const context2d=new Proxy({isPointInPath:()=>true},{get:(o,k)=>o[k]||(()=>{}),set:(o,k,v)=>(o[k]=v,true)});
const els=new Map();const element=()=>({style:{},className:'',classList:{toggle(){}},value:0,textContent:'',clientWidth:1440,clientHeight:620,add(){},append(){},getContext:()=>context2d,addEventListener(){},setAttribute(){},setPointerCapture(){}});
const doc={getElementById(id){if(!els.has(id))els.set(id,element());return els.get(id)},createElement:element};
let lastScene;const ctx={document:doc,window:{},devicePixelRatio:1,Path2D:class{},ResizeObserver:class{observe(){}},requestAnimationFrame(){},performance:{now:()=>0},console};vm.createContext(ctx);
for(const name of ['three.min.js','d3.min.js','topojson.min.js'])vm.runInContext(fs.readFileSync(name,'utf8'),ctx);
ctx.THREE.WebGLRenderer=class{setPixelRatio(){}setClearColor(){}setSize(){}render(scene,camera){lastScene=scene;scene.updateMatrixWorld();camera.updateMatrixWorld()}};
ctx.LAND=JSON.parse(fs.readFileSync('land-50m.json'));ctx.RIVERS=JSON.parse(fs.readFileSync('assets/rivers.json'));ctx.HISTORY=JSON.parse(fs.readFileSync('assets/history.json'));
vm.runInContext(fs.readFileSync('assets/app.js','utf8'),ctx);const app=ctx.window.animation;assert(app.ready);assert.equal(app.duration,124);
for(const t of [0,5,19,35,41,44,50,59,74,82,92,105,113,120,124]){app.seek(t);lastScene.traverse(o=>{for(const v of [...o.position,...o.quaternion,...o.scale])assert(Number.isFinite(v));});const st=app.state();assert(st.date.length>0);console.log(t,st.date,st.chapter)}
console.log('PASS: scene construction, dates, event transitions, finite 3D transforms; browser layout was not tested.');

// ---- R-5 / N-1 / N-2 / N-4 regression tests (added). Each builds its own isolated VM
// environment so the run above (and its stdout, which assets/validation.txt is diffed
// against) is completely unaffected. All new PASS output goes to console.error (stderr)
// so `node validate_scene.cjs 2>/dev/null | diff - assets/validation.txt` stays empty.
function buildEnv(customize){
  const c2d=new Proxy({isPointInPath:()=>true},{get:(o,k)=>o[k]||(()=>{}),set:(o,k,v)=>(o[k]=v,true)});
  const elMap=new Map();
  const mkEl=()=>({style:{},className:'',classList:{toggle(){}},value:0,textContent:'',clientWidth:1440,clientHeight:620,add(){},append(){},getContext:()=>c2d,addEventListener(t,fn){(this._listeners=this._listeners||{})[t]=fn},setAttribute(){},setPointerCapture(){}});
  const d={getElementById(id){if(!elMap.has(id))elMap.set(id,mkEl());return elMap.get(id)},createElement:mkEl};
  let scene;const c={document:d,window:{},devicePixelRatio:1,Path2D:class{},ResizeObserver:class{observe(){}},requestAnimationFrame(){},performance:{now:()=>0},console};
  vm.createContext(c);
  for(const name of ['three.min.js','d3.min.js','topojson.min.js'])vm.runInContext(fs.readFileSync(name,'utf8'),c);
  c.THREE.WebGLRenderer=class{setPixelRatio(){}setClearColor(){}setSize(){}render(s,cam){scene=s;s.updateMatrixWorld();cam.updateMatrixWorld()}};
  c.LAND=JSON.parse(fs.readFileSync('land-50m.json'));c.RIVERS=JSON.parse(fs.readFileSync('assets/rivers.json'));c.HISTORY=JSON.parse(fs.readFileSync('assets/history.json'));
  if(customize)customize(c,d,elMap);
  return {ctx:c,doc:d,els:elMap,getScene:()=>scene};
}
function runApp(env){vm.runInContext(fs.readFileSync('assets/app.js','utf8'),env.ctx);return env.ctx.window.animation}

(function testWebglFailureIsSafe(){
  const env=buildEnv(c=>{c.THREE.WebGLRenderer=class{constructor(){throw new Error('no webgl')}}});
  let threw=false,app;
  try{app=runApp(env)}catch(e){threw=true}
  assert.equal(threw,false,'a WebGLRenderer construction failure must not throw out of assets/app.js');
  assert.equal(app.ready,false,'window.animation.ready must be false when WebGLRenderer construction fails');
  assert.equal(typeof app.error,'string');
  console.error('PASS (added, R-5#1): WebGL failure sets window.animation={ready:false,error} without throwing.');
})();

(function testReducedMotionInitialState(){
  const env=buildEnv(c=>{c.matchMedia=()=>({matches:true})});
  runApp(env);
  assert.equal(env.doc.getElementById('play').textContent,'再生','prefers-reduced-motion:reduce must start paused (#play shows the play-side label)');
  console.error('PASS (added, R-5#2): prefers-reduced-motion:reduce starts paused.');
})();

(function testEventUpdatesAreSparse(){
  const env=buildEnv();
  const app=runApp(env);
  const eventEl=env.els.get('event');
  let writes=0,backing=eventEl.textContent;
  Object.defineProperty(eventEl,'textContent',{configurable:true,get:()=>backing,set(v){writes++;backing=v}});
  const FRAMES=497;
  for(let i=0;i<FRAMES;i++)app.seek(i/FRAMES*app.duration);
  assert(writes<FRAMES/5,`#event should update far less often than once per seek (got ${writes} writes for ${FRAMES} seeks)`);
  console.error(`PASS (added, R-5#3): #event updated ${writes} times across ${FRAMES} seeks (guards against a per-frame-write regression).`);
})();

(function testViewLabelStableOnDragAndArrowKeys(){
  const env=buildEnv();
  const app=runApp(env);
  const view=env.els.get('view');view.textContent='真上から見る'; // matches the static markup's initial value
  const canvasEl=env.els.get('scene');
  canvasEl.onpointerdown({clientX:100,clientY:100,pointerId:1});
  canvasEl.onpointermove({clientX:140,clientY:80});
  canvasEl.onpointerup();
  assert.equal(view.textContent,'真上から見る','dragging must not rewrite #view (regression: N-1/R-9, decision A)');
  const keydown=canvasEl._listeners&&canvasEl._listeners.keydown;
  assert.equal(typeof keydown,'function','keydown handler must be registered via addEventListener');
  let defaultPrevented=false;
  keydown({key:'ArrowLeft',preventDefault:()=>defaultPrevented=true});
  assert.equal(view.textContent,'真上から見る','arrow-key rotation must not rewrite #view (regression: N-1/R-9, decision A)');
  assert(defaultPrevented,'arrow-key handling must still preventDefault (unrelated behavior must be unchanged)');
  console.error('PASS (added, R-5#4): #view label is stable across drag and arrow-key camera moves (decision A).');
})();
