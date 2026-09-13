from pathlib import Path
import json,base64
from fontTools import subset
root=Path('.')
template=Path('assets/template.html').read_text();app=Path('assets/app.js').read_text();hist=Path('assets/history.json').read_text()
texts=template+app+hist
opts=subset.Options();opts.flavor='woff';font=subset.load_font('noto.ttf',opts);sub=subset.Subsetter(options=opts);sub.populate(text=texts);sub.subset(font);subset.save_font(font,'assets/font.woff',opts)
repls={'FONT_DATA':base64.b64encode(Path('assets/font.woff').read_bytes()).decode(),'THREE_CODE':Path('three.min.js').read_text(),'D3_CODE':Path('d3.min.js').read_text(),'TOPO_CODE':Path('topojson.min.js').read_text(),'LAND_JSON':Path('land-50m.json').read_text(),'RIVERS_JSON':Path('assets/rivers.json').read_text(),'HISTORY_JSON':hist,'APP_CODE':app}
for k,v in repls.items():template=template.replace(k,v)
licenses='\n\n'.join(p.name+'\n'+p.read_text() for p in Path('assets/licenses').glob('*.txt'));template=template.replace('</body>', '<script type="text/plain" id="third-party-licenses">'+licenses+'</script></body>');Path('output/eastern-front-3d.html').write_text(template)
print('html',len(template.encode()),'font',Path('assets/font.woff').stat().st_size)
