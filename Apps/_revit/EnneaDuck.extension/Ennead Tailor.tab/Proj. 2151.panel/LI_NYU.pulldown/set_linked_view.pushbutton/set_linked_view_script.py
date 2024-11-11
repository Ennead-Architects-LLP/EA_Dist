#!/usr/bin/python
# -*- coding: utf-8 -*-

__doc__ = "Set linked view for projects by a map."
__title__ = "Set Linked View"

import proDUCKtion # pyright: ignore 
proDUCKtion.validify()

from EnneadTab import ERROR_HANDLE, LOG
from EnneadTab.REVIT import REVIT_APPLICATION, REVIT_VIEW, REVIT_SELECTION
from Autodesk.Revit import DB # pyright: ignore 

# UIDOC = REVIT_APPLICATION.get_uidoc()
DOC = REVIT_APPLICATION.get_doc()

MAPPING_DICT_EWING_COLE = {
    "title": "20230633_A24_CENTRAL",
    "level_maps": {
        "L2": "FINAL CONCEPT PLAN - LEVEL 2_SD Decentralized Core",
        "L3": "FINAL CONCEPT PLAN - LEVEL 3_SD Decentralized Core",
        "L4": "FINAL CONCEPT PLAN - LEVEL 4_SD Decentralized Core",
        "L5": "FINAL CONCEPT PLAN - LEVEL 5_SD Decentralized Core",
    }
}

PRINK_LINK_VIEW_NAMES = True


@LOG.log(__file__, __title__)
@ERROR_HANDLE.try_catch_error()
def set_linked_view(doc):
    t = DB.Transaction(doc, __title__)
    t.Start()
    process_link(doc, MAPPING_DICT_EWING_COLE)
    t.Commit()


def process_link(doc,mapping_dict):
    link_doc = REVIT_SELECTION.get_revit_link_doc_by_name(mapping_dict["title"], doc)
    if not link_doc:
        print ("Link doc [{}] not found".format(mapping_dict["title"]))
        return

    
    if PRINK_LINK_VIEW_NAMES:
        linked_views = DB.FilteredElementCollector(link_doc).OfCategory(DB.BuiltInCategory.OST_Views).ToElements()
        linked_views = sorted(list(linked_views), key=lambda x: (str(x.ViewType),x.Name))
        for linked_view in linked_views:
            print("{}:[{}] {}".format(link_doc.Title, linked_view.ViewType, linked_view.Name))
        
    link_instance = REVIT_SELECTION.get_revit_link_instance_by_name(link_doc.Title, doc)
    
    setting = DB.RevitLinkGraphicsSettings ()
    setting.LinkVisibilityType = DB.LinkVisibility.ByLinkView

    all_views = DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Views).ToElements()
    for view in all_views:
        if not hasattr(view, "GenLevel"):
            continue
        if not view.GenLevel:
            continue
        level_name = view.GenLevel.Name
        if level_name not in mapping_dict["level_maps"]:
            continue
        linked_view = REVIT_VIEW.get_view_by_name(mapping_dict["level_maps"][level_name], doc = link_doc)
        if not linked_view:
            print("Linked view [{}] not found".format(mapping_dict["level_maps"][level_name]))
            continue
        setting.LinkedViewId = linked_view.Id
        try:
            view.SetLinkOverrides (link_instance.Id, setting)
            print("Set link view overrides for view [{}] using [{}][{}]".format(output.linkify(view.Id, title=view.Name), link_doc.Title, linked_view.Name))
        except Exception as e:
            print("Error setting link viewoverrides for view [{}]: {}".format(output.linkify(view.Id, title=view.Name), e))




################## main code below #####################
if __name__ == "__main__":
    from pyrevit import script
    output = script.get_output()

    set_linked_view(DOC)





