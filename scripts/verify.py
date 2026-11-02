from pathlib import Path
import json,re,hashlib,sys
ROOT=Path(__file__).resolve().parents[1]
R=ROOT/'reports'

def verify():
    baseline=(R/'baseline.log').read_text();scan=(R/'inserted.log').read_text();bad=(R/'disconnected.log').read_text()
    b=re.search(r'DFT_BASELINE_PASS patterns=(\d+) checks=(\d+)',baseline)
    s=re.search(r'DFT_SCAN_CAPTURE_PASS patterns=(\d+) checks=(\d+)',scan)
    assert b and tuple(map(int,b.groups()))==(256,514)
    assert s and tuple(map(int,s.groups()))==(256,3330)
    assert not re.search(r'(?i)fatal|error|mismatch',baseline+scan)
    assert int((R/'disconnected_exit.txt').read_text())!=0
    assert 'FATAL:' in bad and 'Q_MISMATCH pattern=1' in bad and 'DFT_SCAN_CAPTURE_PASS' not in bad
    insertion=(R/'insertion.log').read_text()
    assert 'DFT_INSERTION_FINISHED' in insertion
    assert "Number of chains: 1" in insertion and "has 8 cells (8 bits)" in insertion
    assert not re.search(r'\[ERROR\s',insertion)
    source=(ROOT/'build/inserted.v').read_text()
    assert len(re.findall(r'\bsky130_fd_sc_hd__sdfxtp_1\s+\S+\s*\(',source))==8
    assert not re.search(r'\bsky130_fd_sc_hd__dfxtp_\d+\s+\S+\s*\(',source)
    chain=json.loads((R/'chain.json').read_text())
    assert len(chain['cells'])==8 and len(set(c['name'] for c in chain['cells']))==8
    assert sorted(chain['head_to_tail_bits'])==list(range(8))
    for prev,nxt in zip(chain['cells'],chain['cells'][1:]): assert prev['pins']['Q']==nxt['pins']['SCD']
    assert chain['cells'][0]['pins']['SCD']=='scan_in'
    assert chain['cells'][-1]['pins']['Q']==chain['scan_output']
    assert set(chain['scan_output']) & set('01234567')
    for file in ('inserted.odb','inserted.def','mapped.v','inserted.v'):
        assert (ROOT/'build'/file).stat().st_size>100
    summary=dict(baseline_patterns=int(b[1]),baseline_checks=int(b[2]),scan_patterns=int(s[1]),scan_checks=int(s[2]),
                 chains=1,scan_cells=8,scan_output=chain['scan_output'],
                 head_to_tail_bits=chain['head_to_tail_bits'],negative_control='Disconnected internal SCD link: pattern 1 expected 01, observed 00, exit 1',
                 mapped_area_um2=290.2784,scope='Functional zero-delay library simulation; no ATPG or routed timing qualification')
    # Read the area from the synthesis report, rather than make the supplied
    # summary value evidence for itself.
    area=re.search(r"Chip area for module[^:]*:\s*([\d.]+)",(R/'synthesis.log').read_text())
    assert area;summary['mapped_area_um2']=float(area[1])
    paths=[ROOT/'rtl/register.v',ROOT/'tests/tb.v',ROOT/'scripts/insert.tcl',ROOT/'build/mapped.v',ROOT/'build/inserted.v',ROOT/'build/simulation_cells.v']
    summary['files_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    (R/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2));print('DFT_INSERTION_FUNCTIONAL_SCAN_AND_NEGATIVE_CONTROL_VERIFIED')

if __name__=='__main__':verify()
