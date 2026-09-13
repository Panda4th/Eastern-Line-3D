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
