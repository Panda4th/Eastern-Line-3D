// T-8: crop land-50m.json to the visible bbox (lon 10-50, lat 42-61.7) + margin, arc-preserving.
// Does not decimate vertices; only drops whole polygons entirely outside the margin and
// garbage-collects arcs no longer referenced. See verify_land_crop.cjs for the correctness gate.
const fs=require('fs'),vm=require('vm');
const ctx={};vm.createContext(ctx);
vm.runInContext(fs.readFileSync('topojson.min.js','utf8'),ctx);
const L=JSON.parse(fs.readFileSync('land-50m.json','utf8'));
const land=L.objects.land;
if(land.type!=='GeometryCollection'||land.geometries.length!==1||land.geometries[0].type!=='MultiPolygon')throw new Error('unexpected land topology shape');
const polys=land.geometries[0].arcs;
const fc=ctx.topojson.feature(L,land);
const coords=fc.features[0].geometry.coordinates;
if(coords.length!==polys.length)throw new Error('polygon count mismatch between decoded feature and raw arcs');
const MARGIN=5,LON0=10-MARGIN,LON1=50+MARGIN,LAT0=42-MARGIN,LAT1=61.7+MARGIN;
function ringBbox(ring){let x0=Infinity,x1=-Infinity,y0=Infinity,y1=-Infinity;for(const[x,y]of ring){if(x<x0)x0=x;if(x>x1)x1=x;if(y<y0)y0=y;if(y>y1)y1=y}return[x0,y0,x1,y1]}
function polyBbox(poly){let x0=Infinity,x1=-Infinity,y0=Infinity,y1=-Infinity;for(const ring of poly){const[a,b,c,d]=ringBbox(ring);if(a<x0)x0=a;if(c>x1)x1=c;if(b<y0)y0=b;if(d>y1)y1=d}return[x0,y0,x1,y1]}
function intersects(bb){const[x0,y0,x1,y1]=bb;return x1>=LON0&&x0<=LON1&&y1>=LAT0&&y0<=LAT1}
const keepIdx=[];for(let i=0;i<polys.length;i++){if(intersects(polyBbox(coords[i])))keepIdx.push(i)}
const keptPolys=keepIdx.map(i=>polys[i]);
const used=new Set();for(const poly of keptPolys)for(const ring of poly)for(const ref of ring)used.add(ref<0?~ref:ref);
const usedSorted=[...used].sort((a,b)=>a-b);
const oldToNew=new Map(usedSorted.map((old,idx)=>[old,idx]));
const newArcs=usedSorted.map(i=>L.arcs[i]);
const remap=ref=>ref<0?~oldToNew.get(~ref):oldToNew.get(ref);
const remappedPolys=keptPolys.map(poly=>poly.map(ring=>ring.map(remap)));
const out={type:'Topology',transform:L.transform,arcs:newArcs,objects:{land:{type:'GeometryCollection',geometries:[{type:'MultiPolygon',arcs:remappedPolys}]}}};
fs.writeFileSync('assets/land-crop.json',JSON.stringify(out)+'\n'); // trailing \n matches land-50m.json, keeps embedded line count stable
console.log('polygons kept',keepIdx.length,'/',polys.length);
console.log('arcs kept',newArcs.length,'/',L.arcs.length);
console.log('bytes original',fs.statSync('land-50m.json').size,'-> cropped',fs.statSync('assets/land-crop.json').size);
