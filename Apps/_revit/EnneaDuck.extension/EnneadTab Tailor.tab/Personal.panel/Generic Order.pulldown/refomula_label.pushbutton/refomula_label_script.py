#!/usr/bin/python
# -*- coding: utf-8 -*-

__doc__ = """Automates the creation and placement of reformula labels in Revit. Streamlines the process of labeling elements according to project standards, improving documentation consistency and efficiency."""
__title__ = "Refomula Label"

import proDUCKtion # pyright: ignore 
proDUCKtion.validify()

from EnneadTab import ERROR_HANDLE, LOG
from EnneadTab.REVIT import REVIT_APPLICATION, REVIT_SELECTION
from Autodesk.Revit import DB # pyright: ignore 

UIDOC = REVIT_APPLICATION.get_uidoc()
DOC = REVIT_APPLICATION.get_doc()


@LOG.log(__file__, __title__)
@ERROR_HANDLE.try_catch_error()
def refomula_label(doc):

    selection = REVIT_SELECTION.get_selection()


    # t = DB.Transaction(doc, __title__)
    # t.Start()
    # pass
    # t.Commit()



################## main code below #####################
if __name__ == "__main__":
    refomula_label(DOC)







