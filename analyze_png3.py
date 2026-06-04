import struct, zlib, os

def read_png_full(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()
    if data[:8] != b'\x89PNG\r\n\x1a\n': return None
    pos = 8; idat_data = b''; chunks = {}
    width = height = color_type = None
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
    return {'width':width,'height':height,'color_type':color_type,'rows':rows, 'num_rows':len(rows)}

for fp in [r'C:\Intel\Desktop\game01\assets\Tiles\Style 1\SimpleStyle1.png', r'C:\Intel\Desktop\game01\assets\Tiles\Style 1\TileStyle1.png']:
    fn = os.path.basename(fp)
    print(f'\\n=== {fn} ===')
    r = read_png_full(fp)
    if not r: continue
    w=r['width']; h=r['height']; rows=r['rows']
    print(f'All visible pixels (alpha>0):')
    count=0
    for y in range(h):
        for x in range(w):
            p = rows[y][x]
            if len(p)>=4 and p[3]>0:
                count+=1
                print(f'  y={y:3d}, x={x:3d}: rgba({p[0]:3d},{p[1]:3d},{p[2]:3d},{p[3]:3d})')
    print(f'Total visible pixels: {count}')
print('\\nDone.')
