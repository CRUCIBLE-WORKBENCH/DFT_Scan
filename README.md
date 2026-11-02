# Eight-bit SKY130 scan insertion

Yosys maps an eight-bit writable register; OpenROAD replaces its flip-flops with scan cells and stitches one chain. The measured baseline passed 514 checks and the inserted netlist passed 3,330 checks across all 256 byte values. A disconnected internal scan link failed the same observer with a nonzero exit. The serial tail reuses `q[0]`; the measured head-to-tail bit order is 1, 2, 3, 5, 7, 6, 4, 0.

The implementation and whitepaper were locally verified on 27 October 2026. **Crucible is beta.** These are bounded engineering demonstrations, with the exclusions below.

## Included files

`rtl/register.v` defines the functional register. `scripts/insert.tcl` performs actual OpenROAD insertion. `chain.py` derives the serial order from saved SCD/Q connectivity. `tests/tb.v` exercises baseline and scan/capture behavior. `verify.py` checks the positive and disconnected-link artifacts.

The reviewed [PDF](docs/DFT_Eight_Bit_Scan_Insertion_Ignytion_A4.pdf) and [editable A4 PowerPoint](docs/DFT_Eight_Bit_Scan_Insertion_Ignytion_A4.pptx) are included. [Compact evidence](evidence/summary.json) records measured outcomes; [document hashes](evidence/documents.sha256.json) bind the final copies. Generated build artifacts and raw logs remain local and are excluded from Git.

## Prerequisites

Use Linux x86-64 or the tested Windows/WSL route, with an existing Crucible beta installation, Bash and Python 3. `crucible.lock` pins the managed tool versions and artifact identities. It does not install the external dependencies described here or establish support for native Windows/macOS/ARM hosts.

Provide a complete SKY130A high-density digital PDK at `$HOME/.ciel/sky130A`, or export `PDKPATH` to its location. Required views are technology LEF, cell LEF, TT 25 C/1.8 V Liberty, functional Verilog and primitives. The runner preprocesses the official Verilog aggregate and extracts only the used module bodies and dependencies unchanged, because the tested aggregate contains an unrelated malformed module. PDK payloads are not vendored. No Python dependencies beyond the standard library are required for engineering verification.

## 1. Choose the correct shell and directory

Run every Linux command below from this repository's root: the directory containing `crucible.toml`, `crucible.lock` and `scripts/`. The tested flow uses **WSL/Linux x86-64**. A Windows PowerShell block is labelled separately. Do not paste a PowerShell block into Bash or run a Bash block in PowerShell.

Crucible must already be installed in that Linux/WSL shell. A PDK, Tcl-capable Magic where required, and native runtime libraries are separate prerequisites; this repository does not provide an installation archive for them. Commands containing `/path/to/...` require your actual dependency location before execution.

## 2. Restore and inspect the Crucible environment

Linux/WSL Bash:

```bash
igny init
igny --version
igny workspace sync
igny status
igny env show dft-scan
igny tool show yosys --env dft-scan
igny tool show openroad --env dft-scan
igny tool show iverilog --env dft-scan
```

`igny init` initializes the outer workbench shell. `workspace sync` reads the supplied lock, acquires missing pinned artifacts and restores the recorded environment. It may download large archives; it does not build this design, provision a PDK, or install every native library. `status` should identify this workspace, and `env show` should list the tools in `dft-scan`. `tool show` establishes the binary/provider resolution before a run.

Stop on an acquisition/binding error and inspect its reported log. A successful version or inventory command is a prerequisite check, not a design PASS. The commands below select the same project environment explicitly through the scripts.

## 3. Configure and check the PDK

Linux/WSL Bash. Replace the example path only if the PDK is outside the default Ciel location:

```bash
export PDKPATH="$HOME/.ciel/sky130A"
# Alternative, after replacing this example with your actual path:
# export PDKPATH='/path/to/sky130A'
test -f "$PDKPATH/libs.ref/sky130_fd_sc_hd/techlef/sky130_fd_sc_hd.tlef"
test -f "$PDKPATH/libs.ref/sky130_fd_sc_hd/lef/sky130_fd_sc_hd.lef"
test -f "$PDKPATH/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib"
test -f "$PDKPATH/libs.ref/sky130_fd_sc_hd/verilog/sky130_fd_sc_hd.v"
test -f "$PDKPATH/libs.ref/sky130_fd_sc_hd/verilog/primitives.v"
python3 --version
igny run --env dft-scan yosys -V
igny run --env dft-scan iverilog -V
```

The engineering scripts require only Python's standard library. The runner uses the supplied LEF/Liberty/Verilog views without editing the PDK. It copies the technology LEF under a distinct build basename to avoid a library-name collision.

## 4. Build the scan design and run every test

Linux/WSL Bash:

```bash
bash scripts/run.sh build
bash scripts/run.sh test
python3 scripts/verify.py
```

`build` checks matching LEF/Liberty cells, maps the functional register, invokes actual OpenROAD scan replacement/stitching, reconstructs SCD/Q order, and creates the disconnected-link scratch netlist. `test` preprocesses the unchanged used PDK functional models, compiles the baseline/inserted/disconnected designs, runs the positive tests and requires a nonzero disconnected-link exit.

## 5. Read the results and negative control

Linux/WSL Bash:

```bash
cat reports/baseline.log
cat reports/inserted.log
cat reports/disconnected_exit.txt
cat reports/disconnected.log
cat reports/chain.json
cat reports/summary.json
tail -n 30 reports/insertion.log
```

The baseline must report `DFT_BASELINE_PASS patterns=256 checks=514`; the inserted run must report `DFT_SCAN_CAPTURE_PASS patterns=256 checks=3330`. The deliberately disconnected internal SCD link must produce `Q_MISMATCH pattern=1`, expected 01 and observed 00, with exit 1. The final observer must print `DFT_INSERTION_FUNCTIONAL_SCAN_AND_NEGATIVE_CONTROL_VERIFIED`.

The chain has eight scan cells and reuses q[0] as its tail. The actual measured head-to-tail q-bit order is 1, 2, 3, 5, 7, 6, 4, 0. `build/inserted.def` and `build/inserted.odb` are placed insertion-stage outputs; they are not routed timing results.

## 6. Troubleshooting

| Symptom | Check and next action |
|---|---|
| Binary not bound | Inspect step 2's `tool show` and lock restoration; use the project environment |
| LEF/Liberty cell mismatch | Inspect `reports/library.json` and supply compatible views from one complete PDK |
| Aggregate PDK Verilog cannot parse | Inspect `build/preprocessed_cells.v` and `reports/simulation_models.json`; the runner selects unchanged used modules rather than inventing models |
| Negative run exits zero | Treat it as a failed guard; inspect `build/disconnected.v` and the same testbench before claiming a pass |
| Missing `chain.vh` or build netlist | Run `build` before `test` |

## 7. Open the whitepaper and check the public Git candidate

Windows PowerShell, from the repository root:

```powershell
Invoke-Item .\docs\DFT_Eight_Bit_Scan_Insertion_Ignytion_A4.pdf
Invoke-Item .\docs\DFT_Eight_Bit_Scan_Insertion_Ignytion_A4.pptx
python --version
python scripts\preflight_git.py
```

The preflight script uses Python's standard library, so `python scripts/preflight_git.py` also works in an existing Python environment. It checks documentation links, the exact document hashes, indexed/unignored paths, shell index modes, selected credential/personal-path patterns and Git whitespace. This is a public-candidate check; it does not rerun EDA tools.

Linux/WSL Git review, after reviewing the files selected by the repository allowlist:

```bash
git status --short
git diff --check
git add -- .
git diff --cached --check
python3 scripts/preflight_git.py
git diff --cached --stat
git diff --cached
```

Do not force-add ignored build products, PDK/runtime payloads, raw logs, local configuration or agent/work notes. The repository contains no invented project-wide licence grant; upstream dependencies retain their own terms.

The following are **manual commit/publication commands**, not steps already performed by this project. Review the staged content and choose your own author identity and public destination first. Run `remote add` only when this repository has no `origin`:

```bash
git branch --show-current
git config user.name
git config user.email
git commit -m "Add verified DFT_Scan demonstration and whitepaper"
PUBLIC_REPOSITORY_URL='REPLACE_WITH_YOUR_PUBLIC_REPOSITORY_URL'
git remote add origin "$PUBLIC_REPOSITORY_URL"
git push -u origin HEAD
```

Replace the destination placeholder before use. A new package is staged on `demo/verified`; the branch command confirms the actual current branch. If `origin` already exists, inspect it with `git remote get-url origin` and skip `remote add`. No commit, remote mutation or push is performed by the reproduction scripts.

## Limits

One clock, one synchronous-reset register and functional zero-delay cell models. No ATPG fault-coverage percentage, routed timing closure, power-aware test, manufactured device or signoff claim. DEF/OpenDB are placed insertion-stage outputs.
