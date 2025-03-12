
__title__ = "2425ReplaceBlocks"
__doc__ = "This button does 2425ReplaceBlocks when left click"

import rhinoscriptsyntax as rs
from EnneadTab import ERROR_HANDLE, LOG
from EnneadTab.RHINO import RHINO_BLOCK
@LOG.log(__file__, __title__)
@ERROR_HANDLE.try_catch_error()
def replace_blocks():
    RHINO_BLOCK.replace_block("Block 02", "Block 01")
    rs.Redraw()
    
if __name__ == "__main__":
    replace_blocks()
