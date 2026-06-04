import struct, zlib, os

def read_png(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        print(f'ERROR: {filepath} not a valid PNG'); return None
    pos = 8; idat_data = b''; chunks = {}
    width = height = bit_depth = color_type = None
    while pos < len(data):
        length = struct.unpack('>I', data[pos:pos+4])[0]
        ctype = data[pos+4:pos+8].decode('ascii', errors='replace')
        cdata = data[pos+8:pos+8+length]
        if ctype == 'IHDR':
            width = struct.unpack('>I', cdata[0:4])[0]
            height = struct.unpack('>I', cdata[4:8])[0]
            bit_depth = cdata[8]; color_type = cdata[9]
            print(f'  IHDR: {width}x{height}, bit_depth={bit_depth}, color_type={color_type}')
        elif ctype == 'PLTE':
            palette = [(cdata[i], cdata[i+1], cdata[i+2]) for i in range(0, len(cdata), 3)]
            chunks['PLTE'] = palette
            print(f'  PLTE: {len(palette)} colors')
        elif ctype == 'IDAT': idat_data += cdata
        elif ctype == 'IEND': break
        pos += 12 + length
    if color_type is None: print('ERROR: No IHDR'); return None
    raw_data = zlib.decompress(idat_data)
    bpp_map = {0:1, 2:3, 3:1, 4:2, 6:4}
    bpp = bpp_map.get(color_type, 1)
    row_size = 1 + width * bpp
    rows = []
    for y in range(height):
        if y*row_size+1 > len(raw_data): break
        row_start = y*row_size+1
        row = []
        for x in range(width):
            px_start = row_start + x*bpp
            if px_start+bpp > len(raw_data): break
            px = raw_data[px_start:px_start+bpp]
            if color_type == 2: row.append((px[0],px[1],px[2]))
            elif color_type == 6: row.append((px[0],px[1],px[2],px[3]))
            elif color_type == 3:
                pal = chunks.get('PLTE',[])
                idx = px[0]
                row.append(pal[idx] if idx < len(pal) else (0,0,0))
            elif color_type == 0: v=px[0]; row.append((v,v,v))
            else: row.append((0,0,0))
        rows.append(row)
    return {'width':width,'height':height,'bit_depth':bit_depth,'color_type':color_type,'rows':rows,'palette':chunks.get('PLTE')}

def cn(*rgb):
    if len(rgb) >= 3:
        r,g,b = rgb[0], rgb[1], rgb[2]
    else:
        return 'unknown'
    if (r,g,b)==(0,0,0): return 'black'
    if (r,g,b)==(255,255,255): return 'white'
    if (r,g,b)==(128,128,128): return 'gray'
    if r>200 and g>200 and b>200: return 'near-white'
    if r<50 and g<50 and b<50: return 'near-black'
    if r>200 and g>100 and b>100: return 'reddish'
    if r>200 and g>200 and b<100: return 'yellowish'
    if r<100 and g>200 and b<100: return 'greenish'
    if r<100 and g<100 and b>200: return 'bluish'
    if r>200 and g<100 and b>200: return 'purplish'
    if abs(r-g)<20 and abs(g-b)<20: return f'gray({r})'
    return f'rgb({r},{g},{b})'

def analyze(fp):
    fn = os.path.basename(fp)
    print('')
    print('='*70)
    print(f'FILE: {fn}')
    print('='*70)
    r = read_png(fp)
    if not r: return
    w=r['width']; h=r['height']; rows=r['rows']
    print('')
    print('--- DIMENSIONS ---')
    print(f'  Width: {w} px')
    print(f'  Height: {h} px')
    ct_names = {0:'Grayscale',2:'RGB',3:'Indexed',4:'Grayscale+Alpha',6:'RGBA'}
    print(f'  Color type: {r["color_type"]} ({ct_names.get(r["color_type"],"Unknown")})')
    print(f'  Bit depth: {r["bit_depth"]}')
    print('')
    print('--- 32-PIXEL COLUMNS ---')
    if w%32==0: print(f'  YES: {w}px width -> {w//32} columns of 32px')
    else: print(f'  NO: {w}px not divisible by 32 (rem: {w%32})')
    dr = min(16, h)
    print('')
    print(f'--- FIRST {dr} ROWS ---')
    for y in range(dr):
        row = rows[y]
        cc = {}
        for p in row:
            k = (p[0], p[1], p[2])
            cc[k] = cc.get(k, 0) + 1
        sc=sorted(cc.items(),key=lambda x:-x[1])
        desc=' | '.join([f'{cn(*c[0])}({c[1]/len(row)*100:.0f}%)' for c in sc[:3]])
        segs=[]; cs=0; cc2=row[0]
        for x in range(1,len(row)):
            if row[x]!=cc2: segs.append((cs,x-1)); cs=x; cc2=row[x]
        segs.append((cs,len(row)-1))
        bar=' '.join([f'[{cn(*row[s[0]][:3])}:{s[1]-s[0]+1}px]' for s in segs[:8]])
        if len(segs)>8: bar+='...'
        print(f'  Row {y:2d}: {desc}')
        print(f'         {bar}')
    print('')
    print('--- DOMINANT COLORS (first ' + str(dr) + ' rows) ---')
    dc={}
    for y in range(dr):
        for p in rows[y]:
            k = (p[0], p[1], p[2])
            dc[k] = dc.get(k, 0) + 1
    total_dc = sum(dc.values())
    for c2,cnt in sorted(dc.items(),key=lambda x:-x[1])[:10]:
        print(f'    {cn(*c2)} ({c2[0]},{c2[1]},{c2[2]}): {cnt/total_dc*100:.1f}% ({cnt} px)')
    print('')
    print('--- PIPE CAP CHECK ---')
    if dr<3: print('  Too few rows'); return
    top_uniform = len(set(rows[0])) <= 2
    bands=[0]
    for y in range(1,dr):
        same=sum(1 for x in range(w) if rows[y][x][:3]==rows[y-1][x][:3])
        if same/w<0.9: bands.append(y)
    bands.append(dr)
    b2=[(bands[i],bands[i+1]-1,bands[i+1]-bands[i]) for i in range(len(bands)-1)]
    print(f'  Horizontal bands: {len(b2)}')
    for b in b2:
        bc={}
        for y in range(b[0],b[1]+1):
            for p in rows[y]:
                k=(p[0],p[1],p[2]); bc[k]=bc.get(k,0)+1
        tb=sorted(bc.items(),key=lambda x:-x[1])[0]
        print(f'    Rows {b[0]}-{b[1]} ({b[2]}r): dominant={cn(*tb[0])} {tb[0]}')
    ind=[]
    if top_uniform: ind.append('Top row uniform (rim edge)')
    else: ind.append('Top row has multiple colors')
    if len(b2)>=3: ind.append(f'{len(b2)} bands suggests rim+body')
    sym=True
    for y in range(dr):
        for x in range(w//2):
            if rows[y][x][:3]!=rows[y][w-1-x][:3]: sym=False; break
        if not sym: break
    if sym: ind.append('Left-right symmetrical')
    gc=sum(1 for y in range(dr) for p in rows[y] if abs(p[0]-p[1])<30 and abs(p[1]-p[2])<30 and 30<p[0]<225)
    if gc/(dr*w)*100>50: ind.append(f'Mostly metallic/gray tones')
    for i in ind: print(f'  [+] {i}')
    print('')
    if len(ind)>=2: print('  VERDICT: Pipe cap LIKELY (rim/edge lines present)')
    else: print('  VERDICT: Pipe cap UNLIKELY')

for f in [r'C:\Intel\Desktop\game01\assets\Tiles\Style 1\SimpleStyle1.png', r'C:\Intel\Desktop\game01\assets\Tiles\Style 1\TileStyle1.png']:
    if os.path.exists(f): analyze(f)
print('')
print('Done.')
