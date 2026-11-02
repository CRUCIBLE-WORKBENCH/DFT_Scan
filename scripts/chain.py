"""Reconstruct the actual serial chain from the inserted gate connectivity."""
from pathlib import Path
import re,json
root=Path(__file__).resolve().parents[1]
text=(root/'build/inserted.v').read_text()
cells=[]
for model,name,body in re.findall(r'(sky130_fd_sc_hd__\w+)\s+(\S+)\s*\((.*?)\);',text,re.S):
    if not model.startswith('sky130_fd_sc_hd__sdf'): continue
    pins={k:re.sub(r'\s+','',v) for k,v in re.findall(r'\.(\w+)\s*\(([^)]+)\)',body)}
    assert pins['SCE']=='scan_enable'
    cells.append(dict(model=model,name=name,pins=pins))
assert len(cells)==8, f'Expected eight scan cells, found {len(cells)}'
chain=[];net='scan_in'
while len(chain)<8:
    found=[c for c in cells if c['pins']['SCD']==net]
    assert len(found)==1, f'Broken or branched chain at {net}'
    cell=found[0];assert cell not in chain,'Scan loop'
    chain.append(cell);net=cell['pins']['Q']
assert re.fullmatch(r'q\[\d\]',net), 'Tail must be an observable functional output'
bits=[]
for c in chain:
    match=re.fullmatch(r'q\[(\d)\]',c['pins']['Q']);assert match
    bits.append(int(match[1]))
assert sorted(bits)==list(range(8))
outbits=bits[::-1]
header=f'localparam integer SCAN_TAIL_BIT={bits[-1]};\nfunction automatic scan_bit;\ninput [7:0] value;\ninput integer index;\nbegin\ncase(index)\n'
header+='\n'.join(f'{i}: scan_bit=value[{bit}];' for i,bit in enumerate(outbits))
header+='\ndefault: scan_bit=1\'bx;\nendcase\nend\nendfunction\n'
(root/'build/chain.vh').write_text(header)
first=cells[0]
# Corrupt one internal scan data connection, leaving valid Verilog and the
# complete functional circuit intact. The same testbench must detect it.
broken,count=re.subn(r'(\.SCD\s*\()(?!scan_in\b)([^)]+)(\))',r"\g<1>1'b0\3",text,count=1)
assert count==1
(root/'build/disconnected.v').write_text(broken)
record=dict(length=8,chains=1,scan_output=net,head_to_tail_bits=bits,shift_out_order=outbits,cells=chain)
(root/'reports/chain.json').write_text(json.dumps(record,indent=2)+'\n')
print('DFT_CHAIN_RECONSTRUCTED',bits)
