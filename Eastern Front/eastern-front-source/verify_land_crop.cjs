// T-8 acceptance gate: the cropped land topology must render an IDENTICAL geoPath string
// to the original, under the exact same projection app.js uses. If this fails, land-crop.json
// must not be adopted (see apply_fixes.py comments / final report).
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const ctx={};vm.createContext(ctx);
for(const name of ['d3.min.js','topojson.min.js'])vm.runInContext(fs.readFileSync(name,'utf8'),ctx);
const {d3,topojson}=ctx;
const LAND=JSON.parse(fs.readFileSync('land-50m.json','utf8'));
const LAND_CROP=JSON.parse(fs.readFileSync('assets/land-crop.json','utf8'));
// Exact projection setup copied from assets/app.js (T-7/T-8 unrelated lines omitted).
const CW=2048, scale=CW/(40*Math.PI/180), merc=lat=>Math.log(Math.tan(Math.PI/4+lat*Math.PI/360));
const CH=Math.round(scale*(merc(61.7)-merc(42)));
const projection=d3.geoMercator().scale(scale).translate([-scale*10*Math.PI/180,scale*merc(61.7)]).clipExtent([[0,0],[CW,CH]]);
const geoPath=d3.geoPath(projection);
const landOrig=topojson.feature(LAND,LAND.objects.land);
const landCrop=topojson.feature(LAND_CROP,LAND_CROP.objects.land);
const pathOrig=geoPath(landOrig);
const pathCrop=geoPath(landCrop);
assert.strictEqual(typeof pathOrig,'string');
assert.strictEqual(pathOrig.length>0,true);
assert.strictEqual(pathCrop,pathOrig);
console.log('PASS: land-crop.json geoPath output is byte-identical to land-50m.json for the app projection.');
console.log('path length',pathOrig.length);
