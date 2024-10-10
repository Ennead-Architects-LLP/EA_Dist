#!/usr/bin/python
# -*- coding: utf-8 -*-

__doc__ = "This tool updates life safety parameters in a Revit project, ensuring compliance with occupancy and egress requirements."
__title__ = "Update Life Safety"

import proDUCKtion # pyright: ignore 
proDUCKtion.validify()

from Autodesk.Revit import DB # pyright: ignore 

from EnneadTab import ERROR_HANDLE, LOG
from EnneadTab.REVIT import REVIT_APPLICATION, REVIT_FAMILY, REVIT_LIFE_SAFETY, REVIT_SELECTION


# UIDOC = REVIT_APPLICATION.get_uidoc()
DOC = REVIT_APPLICATION.get_doc()


@LOG.log(__file__, __title__)
@ERROR_HANDLE.try_catch_error()
def update_life_safety(doc):

    data_source = REVIT_LIFE_SAFETY.SpatialDataSource(
                source = "Area",
                area_scheme_name = "Life Safety",
                 para_name_load_per_area = "Rooms_$LS_Occupancy AreaPer",
                 para_name_load_manual = "Rooms_$LS_Occupancy Load_Manual",
                 para_name_target = "Rooms_$LS_Occupancy Load_Target",
                 para_name_egress_id = "Door_$LS_Exit Name",
                 para_name_door_width = "Door_$LS_Clear Width"
                 )

    t = DB.Transaction(doc, "Life Safety Update")
    t.Start()
    REVIT_LIFE_SAFETY.update_life_safety(doc, data_source)
    REVIT_LIFE_SAFETY.purge_tags_on_non_egress_door(doc, 
                                                    tag_family_name="LS Door Data", 
                                                    tag_family_type_name="SD")
    t.Commit()



################## main code below #####################
if __name__ == "__main__":
    update_life_safety(DOC)







