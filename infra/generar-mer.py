#!/usr/bin/env python3
"""Genera el MER editable y SVG desde los metadatos de la BD activa de SGLAB."""
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET
from html import escape

ROOT=Path(__file__).resolve().parents[1]
def rows(sql):
    r=subprocess.run(['docker','compose','exec','-T','db','sh','-c',
        'MYSQL_PWD="$MARIADB_ROOT_PASSWORD" exec mariadb -uroot --batch --skip-column-names --default-character-set=utf8mb4'],
        cwd=ROOT,input=sql,text=True,capture_output=True,check=True)
    return [line.split('\t') for line in r.stdout.splitlines()]

def main():
    columns=rows("SELECT TABLE_NAME,COLUMN_NAME,COLUMN_TYPE,IS_NULLABLE,COLUMN_KEY FROM information_schema.COLUMNS WHERE TABLE_SCHEMA='sglab' ORDER BY TABLE_NAME,ORDINAL_POSITION")
    fk=rows("SELECT CONSTRAINT_NAME,TABLE_NAME,COLUMN_NAME,REFERENCED_TABLE_NAME,REFERENCED_COLUMN_NAME FROM information_schema.KEY_COLUMN_USAGE WHERE TABLE_SCHEMA='sglab' AND REFERENCED_TABLE_NAME IS NOT NULL ORDER BY TABLE_NAME,CONSTRAINT_NAME,ORDINAL_POSITION")
    tables={}
    for table,*field in columns: tables.setdefault(table,[]).append(field)
    order=['usuarios','laboratorio','asignacion_docente','equipo','registro','comentario_laboratorio','comentario','registro_disco','registro_sistema_archivos']
    positions={name:(60+(i%3)*620,110+(i//3)*650) for i,name in enumerate(order)}
    w=440
    mx=ET.Element('mxfile',host='app.diagrams.net');d=ET.SubElement(mx,'diagram',name='Esquema actual',id='actual')
    m=ET.SubElement(d,'mxGraphModel',page='1',pageWidth='1860',pageHeight='2150');root=ET.SubElement(m,'root');ET.SubElement(root,'mxCell',id='0');ET.SubElement(root,'mxCell',id='1',parent='0')
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1860" height="2150" viewBox="0 0 1860 2150">','<rect width="1860" height="2150" fill="#101827"/>','<style>text{font-family:Arial,sans-serif;fill:#e6edf8} .field{font-size:14px} .title{font-size:17px;font-weight:bold} .rel{font-size:12px;paint-order:stroke;stroke:#101827;stroke-width:4px;stroke-linejoin:round}</style>','<text x="60" y="45" font-size="25">SGLAB · Modelo de datos actual</text>','<text x="60" y="75" font-size="14">PK: clave primaria · UQ: única · FK: clave foránea · ?: admite NULL · Las relaciones usan los nombres de campo.</text>']
    links=[];cards=[];sizes={}
    fkfields={(t,c) for _,t,c,_,_ in fk}
    for table in order:
        if table not in tables:continue
        fields=tables[table];x,y=positions[table];h=55+25*len(fields);sizes[table]=h
        labels=[]
        for field,typ,nullable,key in fields:
            tags=[]
            if key=='PRI':tags.append('PK')
            if key=='UNI':tags.append('UQ')
            if (table,field) in fkfields:tags.append('FK')
            if nullable=='YES':tags.append('?')
            short='ENUM' if typ.startswith('enum(') else typ
            labels.append(field+' : '+short+('  ['+', '.join(tags)+']' if tags else ''))
        c=ET.SubElement(root,'mxCell',id=table,value=table.upper()+'\n\n'+'\n'.join(labels),style='rounded=0;whiteSpace=wrap;html=0;align=left;verticalAlign=top;spacing=15;fontFamily=monospace;fontSize=14;fillColor=#182c40;strokeColor=#83acc7;fontColor=#e6edf8;',vertex='1',parent='1');ET.SubElement(c,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h),**{'as':'geometry'})
        cards.extend([f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="#182c40" stroke="#83acc7"/>',f'<text x="{x+14}" y="{y+29}" class="title">{table.upper()}</text>',f'<line x1="{x}" y1="{y+43}" x2="{x+w}" y2="{y+43}" stroke="#83acc7"/>'])
        for i,label in enumerate(labels):cards.append(f'<text x="{x+14}" y="{y+65+i*25}" class="field">{escape(label)}</text>')
    groups={}
    for constraint,table,column,parent,pcol in fk:
        groups.setdefault((constraint,table,parent),[]).append((column,pcol))
    for i,((constraint,child,parent),pairs) in enumerate(groups.items()):
        if child not in positions or parent not in positions:continue
        cols=[v[0] for v in pairs]
        optional=any(f[0] in cols and f[2]=='YES' for f in tables[child])
        unique_child=len(cols)==1 and next(f for f in tables[child] if f[0]==cols[0])[3] in ('PRI','UNI')
        left='0..1' if unique_child else '0..N';right='0..1' if optional else '1'
        label=', '.join(cols)+' → '+', '.join(v[1] for v in pairs)+'  ('+left+' : '+right+')'
        c=ET.SubElement(root,'mxCell',id='fk-'+str(i),value=label,style='edgeStyle=orthogonalEdgeStyle;rounded=0;html=0;endArrow=block;endFill=0;strokeColor=#7197ab;fontColor=#e6edf8;fontSize=11;labelBackgroundColor=#101827;',edge='1',parent='1',source=child,target=parent);ET.SubElement(c,'mxGeometry',relative='1',**{'as':'geometry'})
        x1,y1=positions[child];x2,y2=positions[parent]
        start=(x1+w,y1+70+(i%3)*25);end=(x2+w,y2+70+(i%3)*25);lane=max(start[0],end[0])+22+(i%5)*13
        links.append(f'<path d="M {start[0]} {start[1]} H {lane} V {end[1]} H {end[0]}" fill="none" stroke="#7197ab" stroke-width="1.3"/>')
        links.append(f'<text x="{lane+4}" y="{(start[1]+end[1])/2}" class="rel">{i+1}</text>')
    svg.extend(links);svg.extend(cards)
    # El catálogo completa las relaciones aunque un conector quede detrás de otra tabla.
    svg.append('<text x="60" y="1915" font-size="18">Relaciones (hijo → padre)</text>')
    for i,((_,child,parent),pairs) in enumerate(groups.items()):
        x=60+(i%2)*900;y=1945+(i//2)*24
        label=f'{i+1}. {child} ({", ".join(a for a,b in pairs)}) → {parent}'
        svg.append(f'<text x="{x}" y="{y}" font-size="12">{escape(label)}</text>')
    svg.append('</svg>')
    (ROOT/'docs/MER-SGLAB.drawio').write_bytes(ET.tostring(mx,encoding='utf-8',xml_declaration=True))
    (ROOT/'docs/MER-SGLAB.svg').write_text('\n'.join(svg))
    print(f'MER actualizado: {len(tables)} tablas y {len(groups)} relaciones.')

if __name__=='__main__':main()
