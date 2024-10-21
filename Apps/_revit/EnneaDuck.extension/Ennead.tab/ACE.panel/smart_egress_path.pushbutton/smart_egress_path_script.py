#!/usr/bin/python
# -*- coding: utf-8 -*-

__doc__ = """
1. gather all the egress path family as dict, key is the 
"""
__title__ = "Smart\nEgress Path"

import proDUCKtion # pyright: ignore 
proDUCKtion.validify()

from EnneadTab import ERROR_HANDLE, LOG, SAMPLE_FILE
from EnneadTab.REVIT import REVIT_APPLICATION, REVIT_VIEW, REVIT_FAMILY, REVIT_SCHEDULE
from Autodesk.Revit import DB # pyright: ignore 

# UIDOC = REVIT_APPLICATION.get_uidoc()
DOC = REVIT_APPLICATION.get_doc()
SCHDULE_NAME = "Egress Path Schedule"
EGRESS_PATH_FAMILY_NAME = "Egress Path Marker"
FAMILY_PATH = SAMPLE_FILE.get_file("{}.rfa".format(EGRESS_PATH_FAMILY_NAME))

@LOG.log(__file__, __title__)
@ERROR_HANDLE.try_catch_error()
def smart_egress_path():
    view = REVIT_VIEW.get_view_by_name(SCHDULE_NAME, doc = DOC)
    if view is None:
        view = create_egress_schedule(DOC)

def create_egress_schedule(doc):
    t = DB.Transaction(doc, "Create Egress Schedule")
    t.Start()
    family = REVIT_FAMILY.get_family_by_name(EGRESS_PATH_FAMILY_NAME, load_path_if_not_exist = FAMILY_PATH)

    field_names = ["Family", "Type Mark", "LS_$DETL_Egress Path_Length", "LS_$DETL_Egress Path_PathID", "LS_$DETL_Egress Path_Total"]
    view = REVIT_SCHEDULE.create_schedule(doc, SCHDULE_NAME, field_names, built_in_category = DB.BuiltInCategory.OST_DetailComponents)

    REVIT_SCHEDULE.add_filter_to_schedule(view, "Family", DB.ScheduleFilterType.Equal, family.Id)
    t.Commit()




################## main code below #####################
if __name__ == "__main__":
    smart_egress_path()







