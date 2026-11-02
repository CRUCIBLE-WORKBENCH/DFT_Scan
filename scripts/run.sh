#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PDKPATH="${PDKPATH:-$HOME/.ciel/sky130A}"
LIB="$PDKPATH/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib"
HD="$PDKPATH/libs.ref/sky130_fd_sc_hd"
mkdir -p build reports
case "${1:-build}" in
  build)
    python3 scripts/library.py
    EXCLUDE=$(cat build/exclude.txt)
    cat >build/synth.ys <<EOF
read_verilog rtl/register.v
synth -top register8 -noabc
dfflibmap -liberty $LIB
abc -liberty $LIB ${EXCLUDE:+-dont_use $EXCLUDE}
hilomap -singleton -hicell sky130_fd_sc_hd__conb_1 HI -locell sky130_fd_sc_hd__conb_1 LO
clean
write_verilog -noattr -noexpr build/mapped.v
write_json build/mapped.json
stat -liberty $LIB
EOF
    igny run --env dft-scan yosys -l reports/synthesis.log build/synth.ys >reports/synthesis_console.log 2>&1
    igny run --env dft-scan openroad -exit scripts/insert.tcl >reports/insertion.log 2>&1
    python3 scripts/chain.py
    ;;
  test)
    igny run --env dft-scan iverilog -E -DFUNCTIONAL '-DUNIT_DELAY=#0' -o build/preprocessed_cells.v "$HD/verilog/sky130_fd_sc_hd.v"
    python3 scripts/simulation_models.py
    igny run --env dft-scan iverilog -g2012 -s tb -o build/baseline.vvp tests/tb.v rtl/register.v
    igny run --env dft-scan vvp build/baseline.vvp >reports/baseline.log 2>&1
    for mode in inserted disconnected; do
      igny run --env dft-scan iverilog -g2012 -DFUNCTIONAL -DSCAN -Ibuild -s tb \
        -o "build/$mode.vvp" tests/tb.v "build/$mode.v" "$HD/verilog/primitives.v" build/simulation_cells.v
    done
    igny run --env dft-scan vvp build/inserted.vvp >reports/inserted.log 2>&1
    set +e
    igny run --env dft-scan vvp build/disconnected.vvp >reports/disconnected.log 2>&1
    status=$?
    set -e
    echo "$status" >reports/disconnected_exit.txt
    if [ "$status" -eq 0 ]; then echo 'Disconnected-chain test incorrectly passed' >&2; exit 1; fi
    ;;
  *) exit 2 ;;
esac
