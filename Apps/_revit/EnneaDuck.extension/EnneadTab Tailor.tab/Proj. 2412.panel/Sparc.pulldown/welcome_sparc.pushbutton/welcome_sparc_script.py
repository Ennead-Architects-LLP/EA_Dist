#!/usr/bin/python
# -*- coding: utf-8 -*-

__doc__ = """Displays a welcome message and project-specific information for the Sparc project in Revit. Use this tool to onboard team members, share project guidelines, or provide quick access to essential resources."""
__title__ = "Welcome Sparc"

import proDUCKtion # pyright: ignore 
proDUCKtion.validify()

from EnneadTab import ERROR_HANDLE, LOG
# from EnneadTab.REVIT import REVIT_APPLICATION
from Autodesk.Revit import DB # pyright: ignore 

# UIDOC = REVIT_APPLICATION.get_uidoc()
# DOC = REVIT_APPLICATION.get_doc()


@LOG.log(__file__, __title__)
@ERROR_HANDLE.try_catch_error()
def welcome_sparc():
    pass


    # t = DB.Transaction(doc, __title__)
    # t.Start()
    # pass
    # t.Commit()



################## main code below #####################
if __name__ == "__main__":
    welcome_sparc()







