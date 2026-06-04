import struct, zlib, os

def read_png_full(filepath):
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
        elif ctype == 'PLTE':
            chunks['PLTE'] = [(cdata[i], cdata[i+1], cdata[i+2]) for i in range(0, len(cdata), 3)]
        elif ctype == 'IDAT': idat_data += cdata
        elif ctype == 'IEND': break
        pos += 12 + length
    if color_type is None: return None
    raw_data = zlib.decompress(idat_data)
    bpp_map = {0:1,2:3,3:1,4:2,6:4}
    bpp = bpp_map[color_type]
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
            if color_type == 6: row.append((px[0],px[1],px[2],px[3]))
            elif color_type == 2: row.append((px[0],px[1],px[2],255))
            elif color_type == 3:
                pal = chunks.get('PLTE',[]); idx=px[0]
                c = pal[idx] if idx<len(pal) else (0,0,0)
                row.append((c[0],c[1],c[2],255))
            elif color_type == 0: v=px[0]; row.append((v,v,v,255))
            else: row.append((0,0,0,0))
        rows.append(row)
    return {'width':width,'height':height,'color_type':color_type,'rows':rows}

def cn(*rgb):
    if len(rgb)>=3: r,g,b = rgb[0],rgb[1],rgb[2]
    else: return '?'
    if (r,g,b)==(0,0,0): return 'black'
    if (r,g,b)==(255,255,255): return 'white'
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
    r = read_png_full(fp)
    if not r: return
    w=r['width']; h=r['height']; rows=r['rows']
    
    # Check alpha usage
    non_zero_alpha = 0
    total_px = w * h
    for row in rows:
        for p in row:
            if len(p)>=4 and p[3]>0: non_zero_alpha += 1
    print(f'')
    print(f'  Pixels with alpha>0: {non_zero_alpha}/{total_px} ({non_zero_alpha/total_px*100:.1f}%)')
    print(f'  Pixels fully transparent: {total_px-non_zero_alpha}/{total_px} ({(total_px-non_zero_alpha)/total_px*100:.1f}%)')
    
    print('')
    print('--- DIMENSIONS ---')
    print(f'  Width:  {w} px')
    print(f'  Height: {h} px')
    ct_names = {0:'Grayscale',2:'RGB',3:'Indexed',4:'Grayscale+Alpha',6:'RGBA'}
    print(f'  Color type: {r["color_type"]} ({ct_names.get(r["color_type"],"Unknown")})')
    print('')
    print('--- 32-PIXEL COLUMNS ---')
    if w%32==0: print(f'  YES: {w}px width -> {w//32} columns of 32px')
    else: print(f'  NO: {w}px not divisible by 32 (rem: {w%32})')
    
    dr = min(16, h)
    print('')
    print(f'--- FIRST {dr} ROWS (alpha-aware) ---')
    for y in range(dr):
        row = rows[y]
        cc = {}; tc = 0
        for p in row:
            if len(p)>=4 and p[3]==0: tc += 1
            else:
                k=(p[0],p[1],p[2]); cc[k]=cc.get(k,0)+1
        trans_pct = tc/len(row)*100
        sc=sorted(cc.items(),key=lambda x:-x[1])
        desc=f'transparent({trans_pct:.0f}%)'
        if sc:
            desc += ' | ' + ' | '.join([f'{cn(*c[0])}({c[1]/len(row)*100:.0f}%)' for c in sc[:3]])
        segs=[]; cs=0; cc2=row[0]
        for x in range(1,len(row)):
            if row[x]!=cc2: segs.append((cs,x-1,row[cs])); cs=x; cc2=row[x]
        segs.append((cs,len(row)-1,row[cs]))
        bar=''
        for s in segs[:8]:
            p=s[2]
            if len(p)>=4 and p[3]==0: label='transparent'
            else: label=cn(*p[:3])
            bar += f'[{label}:{s[1]-s[0]+1}px] '
        if len(segs)>8: bar+='...'
        print(f'  Row {y:2d}: {desc}')
        if sc:
            print(f'         non-transparent: {bar}')
    
    print('')
    print('--- DETAILED ROW 0 PIXEL COLUMNS ---')
    row0 = rows[0]
    # Show first few pixels of row 0
    print(f'  First 10 pixels of row 0:')
    for x in range(min(10,w)):
        p = row0[x]
        if len(p)>=4 and p[3]==0: print(f'    x={x}: transparent')
        else: print(f'    x={x}: rgba({p[0]},{p[1]},{p[2]},{p[3]}) = {cn(*p[:3])}')
    
    print('')
    print('--- VISIBLE PIXEL POSITIONS (row 0, alpha>0) ---')
    for x in range(w):
        p = row0[x]
        if len(p)>=4 and p[3]>0:
            print(f'    x={x:3d}: rgba({p[0]:3d},{p[1]:3d},{p[2]:3d},{p[3]:3d}) = {cn(*p[:3])}')
    
    # Also look at row 15 for SimpleStyle1
    if dr > 15:
        print('')
        print('--- VISIBLE PIXEL POSITIONS (row 15, alpha>0) ---')
        row15 = rows[15]
        for x in range(w):
            p = row15[x]
            if len(p)>=4 and p[3]>0:
                print(f'    x={x:3d}: rgba({p[0]:3d},{p[1]:3d},{p[2]:3d},{p[3]:3d}) = {cn(*p[:3])}')

for f in [r'C:\Intel\Desktop\game01\assets\Tiles\Style 1\SimpleStyle1.png', r'C:\Intel\Desktop\game01\assets\Tiles\Style 1\TileStyle1.png']:
    if os.path.exists(f): analyze(f)
print('')
print('Done.')
