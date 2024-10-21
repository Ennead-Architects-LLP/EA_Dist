#!/usr/bin/python
# -*- coding: utf-8 -*-

__doc__ = """
1. gather all the egress path family as dict, key is the 
"""
__title__ = "Smart\nEgress Path"

import proDUCKtion # pyright: ignore 
proDUCKtion.validify()

import traceback
from EnneadTab import ERROR_HANDLE, LOG, SAMPLE_FILE
from EnneadTab.REVIT import REVIT_APPLICATION, REVIT_LIFE_SAFETY
from Autodesk.Revit import DB # pyright: ignore 
# UIDOC = REVIT_APPLICATION.get_uidoc()
DOC = REVIT_APPLICATION.get_doc()
SCHDULE_NAME = "Egress Path Schedule"
EGRESS_PATH_FAMILY_NAME = "Egress Path Marker"
EGRESS_PATH_TAG_FAMILY_NAME = "Egress Path Tag"
FAMILY_PATH = SAMPLE_FILE.get_file("{}.rfa".format(EGRESS_PATH_FAMILY_NAME))
TAG_FAMILY_PATH = SAMPLE_FILE.get_file("{}.rfa".format(EGRESS_PATH_TAG_FAMILY_NAME))
@LOG.log(__file__, __title__)
@ERROR_HANDLE.try_catch_error()
def smart_egress_path(doc):

    para_name_egress_path_path_id = "EgressPath_ID"
    para_name_egress_path_total = "EgressPath_TotalLength"
    REVIT_LIFE_SAFETY.smart_egress_path(doc, 
                                        SCHDULE_NAME, 
                                        EGRESS_PATH_FAMILY_NAME, 
                                        FAMILY_PATH, 
                                        EGRESS_PATH_TAG_FAMILY_NAME,
                                        TAG_FAMILY_PATH,
                                        para_name_egress_path_path_id, 
                                        para_name_egress_path_total)


################## main code below #####################
if __name__ == "__main__":
    smart_egress_path(DOC)







