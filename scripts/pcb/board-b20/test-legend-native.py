"""Native actual-board regression for B20-only typography and outline guards.

usage: kicad-python test-legend-native.py PCB OUTPUT_DIRECTORY
No source board is saved; native DRC remains separate.
"""
from pathlib import Path
import sys
from finish_details import artwork, p, save_preserving_projects

source, output = Path(sys.argv[1]), Path(sys.argv[2])
output.mkdir(parents=True, exist_ok=True)
source_project=source.with_suffix('.kicad_pro');original_project=source_project.read_bytes()
board=p.LoadBoard(str(source));artwork(board)
first=output/'once.kicad_pcb';first.with_suffix('.kicad_pro').write_bytes(original_project)
save_preserving_projects(board,first,source)
artwork(board);save_preserving_projects(board,first,source)
second=first.read_bytes()
board=p.LoadBoard(str(source));artwork(board);save_preserving_projects(board,first,source)
if first.read_bytes()!=second:raise RuntimeError('Artwork is not deterministic/idempotent')

def reject(mutate):
    board=p.LoadBoard(str(source));mutate(board)
    try:artwork(board)
    except RuntimeError:return
    raise RuntimeError('Negative control accepted changed geometry/contract')

def terminal(board):return next(f for f in board.GetFootprints() if f.GetReference()=='J6')
def bad_outline(board):
    shape=next(g for g in terminal(board).GraphicalItems() if isinstance(g,p.PCB_SHAPE) and g.GetLayer()==p.F_SilkS)
    shape.SetWidth(p.FromMM(.13))
def bad_net(board):next(q for q in terminal(board).Pads() if q.GetNumber()=='2').SetNet(board.FindNet('GND'))
def bad_label(board):
    label=next(t for t in board.GetDrawings() if isinstance(t,p.PCB_TEXT) and t.GetLayer()==p.F_SilkS and t.GetText()=='-12V')
    label.SetPosition(label.GetPosition()+p.VECTOR2I(p.FromMM(.1),0))
def damaged_clip(board):
    artwork(board)
    shape=next(g for g in terminal(board).GraphicalItems() if isinstance(g,p.PCB_SHAPE) and g.GetLayer()==p.F_SilkS)
    shape.SetEnd(shape.GetEnd()+p.VECTOR2I(p.FromMM(.1),0))
for mutate in [bad_outline,bad_net,bad_label,damaged_clip]:reject(mutate)
if first.with_suffix('.kicad_pro').read_bytes()!=original_project:raise RuntimeError('Replay changed output project')
if source_project.read_bytes()!=original_project:raise RuntimeError('Read-only replay changed source project')
print('PASS: deterministic/idempotent artwork; negative outline, net, label-location and clipped-shape controls')
