import json,math,os,subprocess,sys,time
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
from pathlib import Path
W,H=1440,870;TOP=92;SH=595;CW,CH=1536,1251;MW=38.;MH=MW*CH/CW
D=json.load(open('assets/history.json'));K=D['keyframes'];total=0
BLACK=(17,19,24);RED=(201,37,53);BG=(238,234,225);INK=(34,44,47);MUTED=(87,98,93)
fontpath='noto.ttf'
fonts={s:ImageFont.truetype(fontpath,s) for s in [11,12,13,14,15,16,18,21,23,27,28,32]}
for f in fonts.values():
 try:f.set_variation_by_axes([460])
 except Exception:pass
def txt(d,p,s,size=14,fill=INK,anchor=None,stroke=0):d.text(p,s,font=fonts[size],fill=fill,anchor=anchor,stroke_width=stroke,stroke_fill=BG)
def merc(l):return math.log(math.tan(math.pi/4+l*math.pi/360))
def px(ll):return np.array([(ll[0]-10)/40*CW,(merc(61.7)-merc(ll[1]))/(merc(61.7)-merc(42))*CH])
def ll(p,y=.08):q=px(p);return np.array([(q[0]/CW-.5)*MW,y,(q[1]/CH-.5)*MH])
def resample(pts,n=110):
 pts=np.array(pts);lens=np.r_[0,np.cumsum(np.linalg.norm(np.diff(pts,axis=0),axis=1))];ts=np.linspace(0,lens[-1],n);return np.column_stack([np.interp(ts,lens,pts[:,i]) for i in range(3)])
for k in K:
 k['t']=total;total+=k['seconds'];k['ms']=np.datetime64(k['date'],'ms').astype(np.int64);k['samples']=resample([ll(p) for p in k['line']])
endt=K[-1]['t']
def timeof(date):
 ms=np.datetime64(date,'ms').astype(np.int64)
 for a,b in zip(K,K[1:]):
  if a['ms']<=ms<=b['ms']:return a['t']+(ms-a['ms'])/(b['ms']-a['ms'])*(b['t']-a['t'])
 return 0 if ms<K[0]['ms'] else endt
for a in D['arrows']:a['st']=timeof(a['start']);a['et']=timeof(a['end']);a['points']=np.array([ll(p) for p in a['pts']]);a['points'][1,1]=1.1
mask=Image.new('L',(CW,CH),0);md=ImageDraw.Draw(mask)
for ring in json.load(open('assets/map-rings.json'))['rings']:md.polygon([(x*.75,y*.75) for x,y in ring],fill=255)
base=Image.new('RGB',(CW,CH),(189,212,216));base.paste((230,226,211),(0,0,CW,CH),mask);bd=ImageDraw.Draw(base)
for ring in json.load(open('assets/map-rings.json'))['rings']:bd.line([(x*.75,y*.75) for x,y in ring],fill=(143,167,158),width=1)
for lon in range(10,51,5):bd.line([tuple(px([lon,42])),tuple(px([lon,61.7]))],fill=(179,191,180),width=1)
for lat in range(45,61,5):bd.line([tuple(px([10,lat])),tuple(px([50,lat]))],fill=(179,191,180),width=1)
for feat in json.load(open('assets/rivers.json'))['features']:
 coords=feat['geometry']['coordinates'];coords=[coords] if feat['geometry']['type']=='LineString' else coords
 for points in coords:bd.line([tuple(px(p)) for p in points],fill=(129,173,183),width=2)
# Overlay only the theatre front, never fill political control areas.
def pixpts(ps):return np.column_stack([(ps[:,0]/MW+.5)*CW,(ps[:,2]/MH+.5)*CH])
def normals(ps):
 tangent=np.vstack([ps[1]-ps[0],ps[2:]-ps[:-2],ps[-1]-ps[-2]]);n=np.column_stack([tangent[:,2],np.zeros(len(ps)),-tangent[:,0]]);return n/(np.linalg.norm(n,axis=1)[:,None]+1e-12)
def mapframe(front,t):
 n=normals(front);overlay=Image.new('RGBA',(CW,CH),(0,0,0,0));od=ImageDraw.Draw(overlay)
 for side,col in [(-1,(*BLACK,52)),(1,(*RED,46))]:
  a=pixpts(front);b=pixpts(front+n*.66*side);od.polygon([tuple(p) for p in np.vstack([a,b[::-1]])],fill=col)
 # fixed invasion start line, broken into dashes
 ps=pixpts(K[0]['samples'])
 for i in range(0,len(ps)-2,3):od.line([tuple(p) for p in ps[i:i+2]],fill=(90,88,78,90),width=1)
 if t<endt:
  ps=pixpts(front);od.line([tuple(p) for p in ps],fill=(255,255,255,235),width=5,joint='curve')
  for side,col in [(-1,(*BLACK,255)),(1,(*RED,255))]:od.line([tuple(p) for p in pixpts(front+n*.055*side)],fill=col,width=2,joint='curve')
 alpha=np.minimum(np.array(overlay.getchannel('A')),np.array(mask));overlay.putalpha(Image.fromarray(alpha));img=base.copy();img.paste(overlay,(0,0),overlay);return img,n

def state(t):
 i=max(j for j,k in enumerate(K) if k['t']<=min(t,total));a=K[i];b=K[min(i+1,len(K)-1)];u=(t-a['t'])/(b['t']-a['t']) if b['t']!=a['t'] else 0;u=min(1,max(0,u));return i,a,b,u,a['samples']*(1-u)+b['samples']*u

def camera(t):
 az=-.09+.10*math.sin(t/total*math.pi*2);el=.98+.035*math.sin(t/total*math.pi*2);dist=48
 eye=np.array([math.sin(az)*math.cos(el)*dist,math.sin(el)*dist,math.cos(az)*math.cos(el)*dist]);back=eye/np.linalg.norm(eye);right=np.cross([0,1,0],back);right/=np.linalg.norm(right);up=np.cross(back,right);rot=np.stack([right,up,back]);f=SH/(2*math.tan(math.radians(39)/2))
 def project(points):
  p=np.asarray(points);c=(p-eye)@rot.T;z=-c[...,2];return np.stack([W/2+f*c[...,0]/z,TOP+SH/2-f*c[...,1]/z],axis=-1)
 return project,eye,az

def perspective(image,src,dst):
 A=[];b=[]
 for (x,y),(u,v) in zip(dst,src):A.extend([[x,y,1,0,0,0,-u*x,-u*y],[0,0,0,x,y,1,-v*x,-v*y]]);b.extend([u,v])
 co=np.linalg.solve(np.array(A),np.array(b));return image.transform((W,H),Image.Transform.PERSPECTIVE,co,Image.Resampling.BILINEAR)

# Box meshes rendered from 3D vertices; front of every tank is its barrel (+local X).
BOXES=[(0,.13,0,.63,.22,.39,1), (0,.075,-.25,.70,.16,.13,.68),(0,.075,.25,.70,.16,.13,.68),(-.04,.31,0,.30,.16,.26,1.15),(.29,.34,0,.44,.055,.055,1.2)]
FACES=[[0,1,2,3],[4,7,6,5],[0,4,5,1],[1,5,6,2],[2,6,7,3],[3,7,4,0]]
def tank_faces(pos,angle,color,project,eye,scale=1):
 ca,sa=math.cos(angle),math.sin(angle);rot=np.array([[ca,0,-sa],[0,1,0],[sa,0,ca]]);out=[]
 for x,y,z,a,b,c,shade in BOXES:
  v=np.array([[x-a/2,y-b/2,z-c/2],[x+a/2,y-b/2,z-c/2],[x+a/2,y-b/2,z+c/2],[x-a/2,y-b/2,z+c/2],[x-a/2,y+b/2,z-c/2],[x+a/2,y+b/2,z-c/2],[x+a/2,y+b/2,z+c/2],[x-a/2,y+b/2,z+c/2]])*scale@rot.T+pos
  vv=project(v)
  for face in FACES:
   p=v[face];normal=np.cross(p[1]-p[0],p[2]-p[1]);normal/=np.linalg.norm(normal)+1e-12;center=p.mean(axis=0)
   # draw all faces by depth sorting (small stylized solid models)
   light=.73+.32*max(0,float(np.dot(normal,np.array([-.4,.85,.3]))));col=tuple(int(max(0,min(255,c*shade*light+7))) for c in color)
   out.append((np.linalg.norm(center-eye),[tuple(p) for p in vv[face]],col))
 return out

def bezier(pts,u):return (1-u)**2*pts[0]+2*(1-u)*u*pts[1]+u*u*pts[2]
def label(d,p,s,size=13,fill=(51,64,60),box=False):
 bbox=d.textbbox((0,0),s,font=fonts[size]);tw=bbox[2]-bbox[0];th=size+7;x=int(p[0]-tw/2);y=int(p[1]-th/2)
 if box:d.rounded_rectangle((x-5,y-2,x+tw+5,y+th+2),radius=3,fill=(248,236,214))
 txt(d,(x,y),s,size,fill,stroke=1 if not box else 0)

def inset(im,t,rawdate):
 spec=None
 if '1942-11-18'<=rawdate<'1943-02-02':spec=('スターリングラード周辺',[43.95,48.75],3.8,2.55,['de','su'])
 elif '1943-07-05'<=rawdate<'1943-08-23':spec=('クルスク突出部',[36.05,51.65],3.2,2.7,['de','su'])
 elif '1945-04-16'<=rawdate<'1945-05-03':spec=('ベルリン周辺',[13.75,52.35],2.8,1.7,['su'])
 if spec is None:return
 name,center,dlon,dlat,sides=spec;x,y,iw,ih=42,220,292,224
 nw=px([center[0]-dlon/2,center[1]+dlat/2]);se=px([center[0]+dlon/2,center[1]-dlat/2]);crop=base.crop((*nw,*se)).resize((iw,ih),Image.Resampling.BICUBIC)
 lay=Image.new('RGB',(iw,ih));lay.paste(crop);ld=ImageDraw.Draw(lay)
 def ip(p):return (px(p)-nw)/(se-nw)*np.array([iw,ih])
 def fromworld(p):return (pixpts(np.array(p).reshape(-1,3))-nw)/(se-nw)*[iw,ih]
 if rawdate<'1943-02-02':
  # Display the pocket only after the pincers have joined on November 23.
  if rawdate>='1942-11-23':
   cp=ip([44.15,48.77]);ld.ellipse((cp[0]-25,cp[1]-29,cp[0]+25,cp[1]+29),outline=RED,width=3);ld.rectangle((cp[0]-9,cp[1]-6,cp[0]+9,cp[1]+6),fill=BLACK);label(ld,cp+[0,46],'包囲されたドイツ軍',11,fill=BLACK)
  else:
   ld.line([tuple(ip(p)) for p in [[43.6,49.4],[44.5,48.8],[44.4,48.5],[44.6,48.2]]],fill=BLACK,width=3)
  routes=[a for a in D['arrows'] if a['start']=='1942-11-19']
  for a in routes:
   q=min(1,max(0,(t-a['st'])/(timeof('1942-11-23')-a['st'])));q=max(.005,q);ps=fromworld([bezier(a['points'],z) for z in np.linspace(0,q,60)]);ld.line([tuple(p) for p in ps],fill=RED,width=5,joint='curve');tip=ps[-1];v=ps[-1]-ps[-2];v/=np.linalg.norm(v)+1e-9;n=np.array([-v[1],v[0]]);ld.polygon([tuple(tip+v*7),tuple(tip-v*7+n*6),tuple(tip-v*7-n*6)],fill=RED)
  cp=ip([44.513,48.708]);ld.ellipse((cp[0]-3,cp[1]-3,cp[0]+3,cp[1]+3),fill=(90,104,87));label(ld,cp+[12,-19],'市街',12)
 elif name.startswith('クルスク'):
  line=[[36.4,52.8],[35.6,52.3],[34.9,51.7],[35.5,51.0],[36.6,50.7]];ld.line([tuple(ip(p)) for p in line],fill=BLACK,width=3);routes=[a for a in D['arrows'] if a['start']=='1943-07-05'];cp=ip([36.194,51.737]);ld.ellipse((cp[0]-3,cp[1]-3,cp[0]+3,cp[1]+3),fill=RED);label(ld,cp+[0,-21],'クルスク',12)
  for a in routes:
   q=min(1,max(.02,(t-a['st'])/(a['et']-a['st'])));ps=fromworld([bezier(a['points'],z) for z in np.linspace(0,q,50)]);ld.line([tuple(p) for p in ps],fill=BLACK,width=5);tip=ps[-1];v=ps[-1]-ps[-2];v/=np.linalg.norm(v)+1e-9;n=np.array([-v[1],v[0]]);ld.polygon([tuple(tip+v*7),tuple(tip-v*7+n*6),tuple(tip-v*7-n*6)],fill=BLACK)
  label(ld,[iw/2,ih-23],'南北の攻撃は貫通せず',12,fill=BLACK)
 else:
  for a in [a for a in D['arrows'] if a['start']=='1945-04-16']:
   q=min(1,max(.02,(t-a['st'])/(a['et']-a['st'])));ps=fromworld([bezier(a['points'],z) for z in np.linspace(0,q,60)]);ld.line([tuple(p) for p in ps],fill=RED,width=5);tip=ps[-1];v=ps[-1]-ps[-2];v/=np.linalg.norm(v)+1e-9;n=np.array([-v[1],v[0]]);ld.polygon([tuple(tip+v*7),tuple(tip-v*7+n*6),tuple(tip-v*7-n*6)],fill=RED)
  cp=ip([13.405,52.52]);ld.rectangle((cp[0]-6,cp[1]-6,cp[0]+6,cp[1]+6),fill=BLACK);label(ld,cp+[0,22],'ベルリン',12)
 im.paste(lay,(x,y+34));od=ImageDraw.Draw(im);od.rectangle((x,y,x+iw,y+34),fill=(224,222,210));txt(od,(x+11,y+8),name,13);txt(od,(x+iw-10,y+10),'拡大・概略',11,(110,121,104),anchor='ra');od.rectangle((x,y,x+iw,y+34+ih),outline=(190,196,179),width=1)

lastprint=0
def render(t):
 idx,a,b,u,front=state(t);mp,n=mapframe(front,t);project,eye,az=camera(t)
 im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im)
 corners=np.array([[-MW/2,0,-MH/2],[MW/2,0,-MH/2],[MW/2,0,MH/2],[-MW/2,0,MH/2]])
 upper=project(corners);lower=project(corners+[0,-.65,0]);shadow=project(corners+[.35,-.85,.4]);d.polygon([tuple(p) for p in shadow],fill=(199,201,190))
 for ids,col in [([1,2],(113,137,139)),([2,3],(132,152,150)),([3,0],(107,134,136))]:d.polygon([tuple(upper[i]) for i in ids]+[tuple(lower[i]) for i in reversed(ids)],fill=col)
 mapped=perspective(mp.convert('RGBA'),[(0,0),(CW,0),(CW,CH),(0,CH)],upper);im.paste(mapped,(0,0),mapped);d=ImageDraw.Draw(im)
 faces=[]
 if t<endt:
  for side,color in [(-1,BLACK),(1,RED)]:
   for j in np.round(np.linspace(2,len(front)-3,22)).astype(int):
    p=front[j]+n[j]*.43*side;pixel=pixpts(p[None,:])[0];x,y=np.round(pixel).astype(int)
    if 0<=x<CW and 0<=y<CH and mask.getpixel((x,y)):
     direction=n[j]*(-side);faces+=tank_faces(p,math.atan2(direction[2],direction[0]),color,project,eye)
 # Operation arrows are 3D curves. Their tips and moving vehicles follow the same tangent.
 for arrow in D['arrows']:
  q=(t-arrow['st'])/(arrow['et']-arrow['st'])
  if not 0<=q<=1 or t>=endt:continue
  q=max(.025,min(.995,q));points=np.array([bezier(arrow['points'],z) for z in np.linspace(0,q,55)]);path=project(points);color=BLACK if arrow['side']=='de' else RED
  d.line([tuple(p) for p in path],fill=(249,244,230),width=8,joint='curve');d.line([tuple(p) for p in path],fill=color,width=5,joint='curve')
  tip=points[-1];tangent=points[-1]-points[-2];tangent/=np.linalg.norm(tangent);norm=np.cross([0,1,0],tangent);norm/=np.linalg.norm(norm);tri=project(np.array([tip+tangent*.33,tip-tangent*.38+norm*.23,tip-tangent*.38-norm*.23]));d.polygon([tuple(p) for p in tri],fill=color)
  p=bezier(arrow['points'],max(0,q-.12));p[1]=.1;faces+=tank_faces(p,math.atan2(tangent[2],tangent[0]),color,project,eye,1.12)
 pocket_labels=[]
 for name,at,st,et,rx,rz in [('第6軍などの包囲',[44.2,48.75],'1942-11-23','1943-02-02',.44,.34),('クールラント',[22.1,56.9],'1944-10-10','1945-05-09',.73,.5),('東プロイセン',[20.3,54.5],'1945-02-01','1945-04-25',.55,.35)]:
  if timeof(st)<=t<timeof(et):
   center=ll(at);pts=np.array([center+[rx*math.cos(q),.1,rz*math.sin(q)] for q in np.linspace(0,2*math.pi,65)]);d.line([tuple(p) for p in project(pts)],fill=RED,width=3);faces+=tank_faces(center,0,BLACK,project,eye,.72);pocket_labels.append((project(center)+[0,23],name))
 for _,poly,col in sorted(faces,key=lambda x:x[0],reverse=True):d.polygon(poly,fill=col)
 focus=ll(a['focus']);ring=np.array([focus+[.7*math.cos(q),.04,.7*math.sin(q)] for q in np.linspace(0,2*math.pi,65)])
 if t<endt:d.line([tuple(p) for p in project(ring)],fill=(172,139,75),width=1)
 # Name labels use source coordinates and constant screen size.
 for name,lon,lat in D['cities']:
  p=project(ll([lon,lat]));d.ellipse((p[0]-2,p[1]-2,p[0]+2,p[1]+2),fill=(66,83,78));highlight=np.linalg.norm(ll([lon,lat])-focus)<2.5
  offsets={'ハリコフ':(6,8),'クルスク':(-9,-20),'スモレンスク':(-4,-19),'ミンスク':(-6,7),'ケーニヒスベルク':(-23,-15),'プラハ':(-22,5),'ワルシャワ':(-3,7)}
  dx,dy=offsets.get(name,(0,-20));label(d,p+[dx,dy],name,14,box=highlight)
 for p,name in pocket_labels:label(d,p,name,11,fill=(163,29,43),box=True)
 for name,coord in [('バルト海',[18,57.1]),('黒海',[31,43.7]),('コーカサス',[43.4,42.6])]:label(d,project(ll(coord)),name,15,fill=(71,111,118))
 # editorial frame and timeline
 d.rectangle((0,0,W,TOP),fill=BG);d.line((0,TOP,W,TOP),fill=(201,203,193))
 txt(d,(42,14),'EASTERN FRONT  ·  A WAR IN MOTION',11,(112,123,116));txt(d,(42,34),'東部戦線',28);txt(d,(200,45),'1941 — 1945',15,(103,114,107))
 for x,name,color in [(1165,'ドイツ軍',BLACK),(1300,'ソ連軍',RED)]:d.rounded_rectangle((x,42,x+16,58),radius=2,fill=color);txt(d,(x+25,38),name,14)
 ms=round(a['ms']+(b['ms']-a['ms'])*u);rawdate=str(np.datetime64(ms,'ms'))[:10];date=rawdate.replace('-',' / ')
 ev=[e for e in D['events'] if e['date']<=rawdate][-1];title=ev['title'];note=ev['note']
 if '1942-11-19'<=rawdate<'1942-11-23':title='ウラヌス作戦：南北から包囲';note='ソ連軍が突出部の側面を突破。スターリングラード西方での合流を目指す。'
 txt(d,(42,105),date,32);txt(d,(44,151),'主要時点間を補間した概略戦線',11,(105,119,108))
 txt(d,(1360,110),'北 N',11,(91,111,103),anchor='mm');txt(d,(1360,143),'↑',32,(91,111,103),anchor='mm')
 txt(d,(42,644),'黒・赤の帯：各軍側の戦線周辺 ／ 矢印：主な攻勢の方向',11,(75,100,89));txt(d,(42,665),'破線：1941年6月の開始線 ／ 部隊記号の数・大きさは兵力を示さない',11,(75,100,89))
 d.rectangle((0,687,W,H),fill=BG);d.line((0,687,W,687),fill=(201,203,193));txt(d,(42,711),f'{idx+1:02d} / {len(K)}',12,(138,121,92));txt(d,(125,701),title,23);txt(d,(125,740),note,15,MUTED)
 if t>=endt:txt(d,(1388,200),'1945年5月　終戦',27,INK,anchor='ra');txt(d,(1388,242),'ベルリン陥落からドイツ降伏へ',13,MUTED,anchor='ra')
 x0,x1,y=42,1300,803;d.line((x0,y,x1,y),fill=(204,206,194),width=3);d.line((x0,y,x0+(x1-x0)*t/total,y),fill=(161,126,65),width=3);xx=x0+(x1-x0)*t/total;d.ellipse((xx-5,y-5,xx+5,y+5),fill=(161,126,65))
 for yr,dat in [('1941','1941-06-22'),('1942','1942-01-01'),('1943','1943-01-01'),('1944','1944-01-01'),('1945','1945-01-01')]:
  x=x0+(x1-x0)*timeof(dat)/total;d.line((x,798,x,808),fill=(169,175,161));txt(d,(x,818),yr,12,(96,112,100))
 txt(d,(1398,795),f'{int(t)//60}:{int(t)%60:02d} / {total//60}:{total%60:02d}',12,MUTED,anchor='ra')
 txt(d,(1398,840),'概略再構成 · 地理：Natural Earth · 戦況参考：West Point',11,(118,127,118),anchor='ra')
 inset(im,t,rawdate)
 return im

if __name__=='__main__':
 if len(sys.argv)>1 and sys.argv[1]=='preview':
  t=float(sys.argv[2]) if len(sys.argv)>2 else 40;render(t).save('assets/render-preview.png');print('preview',t)
 else:
  fps=24;chunk=int(sys.argv[1]) if len(sys.argv)>1 else -1;start_frame=chunk*744 if chunk>=0 else 0;stop_frame=(chunk+1)*744 if chunk>=0 else total*fps;outfile=f'assets/chunk-{chunk}.mp4' if chunk>=0 else 'output/eastern-front-1941-1945.mp4';proc=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(fps),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',outfile],stdin=subprocess.PIPE)
  start=time.time()
  for i in range(start_frame,stop_frame):
   proc.stdin.write(render(i/fps).tobytes())
   if i%120==0:print(f'{i}/{total*fps} frames; {time.time()-start:.1f}s',flush=True)
  proc.stdin.close();assert proc.wait()==0;print('DONE',outfile,time.time()-start)
