from pathlib import Path
import os,re,json
hd=Path(os.environ['PDKPATH'])/'libs.ref/sky130_fd_sc_hd'
lef=(hd/'lef/sky130_fd_sc_hd.lef').read_text()
lib=(hd/'lib/sky130_fd_sc_hd__tt_025C_1v80.lib').read_text()
masters=set(re.findall(r'(?m)^MACRO\s+(\S+)',lef))
cells=set(re.findall(r'\bcell\s*\(\s*"?([^\s\)"]+)',lib))
excluded=sorted(cells-masters)
Path('build/exclude.txt').write_text(','.join(excluded))
Path('reports/library.json').write_text(json.dumps(dict(lef_masters=len(masters),liberty_cells=len(cells),excluded=excluded,
    scan_masters=sorted(c for c in masters if '__sdf' in c)),indent=2)+'\n')
print('DFT_LIBRARY_INTERSECTION',len(masters),len(cells),'scan:',[c for c in masters if '__sdf' in c])
