#!/usr/bin/python
# -*- coding: utf-8 -*-

__doc__ = """Launches the EnneadTab App Store, providing access to a curated collection of productivity tools, utilities, and extensions for Revit. Users can easily browse, install, and update plugins to enhance their workflow."""
__title__ = "App Store"
__context__ = "zero-doc"

import proDUCKtion # pyright: ignore 
proDUCKtion.validify()

from EnneadTab import ERROR_HANDLE, LOG, EXE
# from EnneadTab.REVIT import REVIT_APPLICATION
from Autodesk.Revit import DB # pyright: ignore 

# UIDOC = REVIT_APPLICATION.get_uidoc()
# DOC = REVIT_APPLICATION.get_doc()


@LOG.log(__file__, __title__)
@ERROR_HANDLE.try_catch_error()
def app_store():
    EXE.try_open_app("AppStore", safe_open=True)


    # t = DB.Transaction(doc, __title__)
    # t.Start()
    # pass
    # t.Commit()



################## main code below #####################
if __name__ == "__main__":
    app_store()







