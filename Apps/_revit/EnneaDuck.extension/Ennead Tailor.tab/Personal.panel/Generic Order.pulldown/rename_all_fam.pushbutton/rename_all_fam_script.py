#!/usr/bin/python
# -*- coding: utf-8 -*-

__doc__ = "Sen Zhang has not writed documentation for this tool, but he should!"
__title__ = "Rename All Fam"

import proDUCKtion # pyright: ignore 
proDUCKtion.validify()

from EnneadTab import ERROR_HANDLE, LOG
from EnneadTab.REVIT import REVIT_APPLICATION
from Autodesk.Revit import DB # pyright: ignore 

UIDOC = REVIT_APPLICATION.get_uidoc()
DOC = REVIT_APPLICATION.get_doc()


@LOG.log(__file__, __title__)
@ERROR_HANDLE.try_catch_error()
def rename_all_fam(doc):


    t = DB.Transaction(doc, __title__)
    t.Start()
    families = list(DB.FilteredElementCollector(doc).OfClass(DB.Family))
    for i, family in enumerate(families):
        original_name = family.Name
        if "_INT" in original_name:
            new_name = original_name.replace("_INT", "_EA")
        if "_EXT" in original_name:
            new_name = original_name.replace("_EXT", "_EA")
        if new_name != original_name:
            count = 0
            while True:
                try:
                    family.Name = new_name
                    print ("{}/{}: {} ---> {}".format(i+1, len(families), original_name, new_name))
                    break
                except Exception as e:
                    print ("Failed to rename {} to {}. Error: {}".format(original_name, new_name, e))
                    new_name = new_name + "*ahhhh"
                    count += 1
                    if count > 5:
                        break
    t.Commit()



################## main code below #####################
if __name__ == "__main__":
    rename_all_fam(DOC)







