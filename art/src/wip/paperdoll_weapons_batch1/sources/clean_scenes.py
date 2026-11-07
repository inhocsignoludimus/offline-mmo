import bpy
from pathlib import Path
R=Path('/workspace/paperdoll_weapons_batch1');T=R/'pkg/tools_src/scenes';T.mkdir(parents=True,exist_ok=True)
for p in sorted((R/'work').glob('*.blend')):
 bpy.ops.wm.open_mainfile(filepath=str(p))
 bpy.ops.outliner.orphans_purge(do_local_ids=True,do_linked_ids=True,do_recursive=True)
 bpy.ops.wm.save_as_mainfile(filepath=str(T/p.name),compress=True)
print('CLEAN_SOURCE_SCENES_DONE')
