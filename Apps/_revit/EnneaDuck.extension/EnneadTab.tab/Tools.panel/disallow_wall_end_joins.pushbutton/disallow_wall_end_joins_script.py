#!/usr/bin/python
# -*- coding: utf-8 -*-

__doc__ = "Disallows wall end joins by wall type. This tool allows you to select specific wall types and disable their end joins, preventing automatic joining behavior at wall endpoints."
__title__ = "Disallow Wall End Joins"

import proDUCKtion # pyright: ignore 
proDUCKtion.validify()

from EnneadTab import ERROR_HANDLE, LOG, NOTIFICATION
from EnneadTab.REVIT import REVIT_APPLICATION, REVIT_SELECTION, REVIT_FORMS
from Autodesk.Revit import DB # pyright: ignore 

UIDOC = REVIT_APPLICATION.get_uidoc()
DOC = REVIT_APPLICATION.get_doc()


@LOG.log(__file__, __title__)
@ERROR_HANDLE.try_catch_error()
def disallow_wall_end_joins_common(doc, wall_types, mode="ui"):
    """
    Common function to disallow wall end joins for given wall types.
    
    Args:
        doc: Revit document
        wall_types: List of wall types to process
        mode: Processing mode ("ui", "selected", "all")
    """
    
    if not wall_types:
        NOTIFICATION.messenger("No wall types to process.")
        return
    
    t = DB.Transaction(doc, __title__)
    t.Start()
    
    processed_count = 0
    failed_count = 0
    
    for wall_type in wall_types:
        try:
            # Disallow end joins for this wall type
            DB.WallJoinUtils.DisallowWallJoinAtEnd(wall_type)
            processed_count += 1
        except Exception as e:
            failed_count += 1
            wall_type_name = wall_type.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM).AsString()
            NOTIFICATION.messenger("Failed to process wall type: {}".format(wall_type_name))
            continue
    
    t.Commit()
    
    # Provide appropriate feedback based on mode
    if mode == "selected":
        NOTIFICATION.messenger("Successfully processed {} wall types from selected walls to disallow end joins. Failed: {}.".format(processed_count, failed_count))
    elif mode == "all":
        NOTIFICATION.messenger("Successfully processed {} wall types to disallow end joins. Failed: {}.".format(processed_count, failed_count))
    else:  # ui mode
        NOTIFICATION.messenger("Successfully processed {} wall types to disallow end joins. Failed: {}.".format(processed_count, failed_count))


@LOG.log(__file__, __title__)
@ERROR_HANDLE.try_catch_error()
def disallow_wall_end_joins_all(doc, uidoc):
    """
    Disallows wall end joins for all wall types in the document.
    """
    
    # Get all wall types in the document
    wall_types = DB.FilteredElementCollector(doc).OfClass(DB.WallType).ToElements()
    
    if not wall_types:
        NOTIFICATION.messenger("No wall types found in the document.")
        return
    
    NOTIFICATION.messenger("Processing all wall types to disallow end joins...")
    disallow_wall_end_joins_common(doc, wall_types, mode="all")


@LOG.log(__file__, __title__)
@ERROR_HANDLE.try_catch_error()
def disallow_wall_end_joins_selected(doc, uidoc):
    """
    Disallows wall end joins for selected walls only.
    """
    
    # Get selected elements
    selection = uidoc.Selection.GetElementIds()
    
    if not selection:
        NOTIFICATION.messenger("Please select walls first.")
        return
    
    # Filter for walls only
    walls = []
    for element_id in selection:
        element = doc.GetElement(element_id)
        if isinstance(element, DB.Wall):
            walls.append(element)
    
    if not walls:
        NOTIFICATION.messenger("No walls found in selection.")
        return
    
    # Get unique wall types from selected walls
    wall_types = set()
    for wall in walls:
        wall_types.add(wall.WallType)
    
    disallow_wall_end_joins_common(doc, list(wall_types), mode="selected")


@LOG.log(__file__, __title__)
@ERROR_HANDLE.try_catch_error()
def disallow_wall_end_joins_with_ui(doc, uidoc):
    """
    Disallows wall end joins with user interface for wall type selection.
    """
    
    # Get all wall types in the document
    wall_types = DB.FilteredElementCollector(doc).OfClass(DB.WallType).ToElements()
    
    if not wall_types:
        NOTIFICATION.messenger("No wall types found in the document.")
        return
    
    # Create selection options
    options = []
    for wall_type in wall_types:
        wall_type_name = wall_type.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM).AsString()
        options.append([wall_type_name, wall_type])
    
    # Let user select wall types
    selected_wall_types = REVIT_FORMS.select_from_list(options, 
                                                      title="Select Wall Types to Disallow End Joins",
                                                      sub_text="Choose which wall types should have end joins disabled:")
    
    if not selected_wall_types:
        NOTIFICATION.messenger("No wall types selected.")
        return
    
    disallow_wall_end_joins_common(doc, selected_wall_types, mode="ui")


@LOG.log(__file__, __title__)
@ERROR_HANDLE.try_catch_error()
def disallow_wall_end_joins_by_name(doc, wall_type_names):
    """
    Disallows wall end joins for specific wall types by name.
    
    Args:
        doc: Revit document
        wall_type_names: List of wall type names to process
    """
    
    # Get all wall types in the document
    all_wall_types = DB.FilteredElementCollector(doc).OfClass(DB.WallType).ToElements()
    
    # Filter wall types by name
    target_wall_types = []
    for wall_type in all_wall_types:
        wall_type_name = wall_type.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM).AsString()
        if wall_type_name in wall_type_names:
            target_wall_types.append(wall_type)
    
    if not target_wall_types:
        NOTIFICATION.messenger("No matching wall types found.")
        return
    
    disallow_wall_end_joins_common(doc, target_wall_types, mode="by_name")


################## main code below #####################
if __name__ == "__main__":
    # Check if there are selected elements
    selection = UIDOC.Selection.GetElementIds()
    
    if selection:
        # If elements are selected, process only those wall types
        disallow_wall_end_joins_selected(DOC, UIDOC)
    else:
        # If nothing is selected, show UI for wall type selection
        disallow_wall_end_joins_with_ui(DOC, UIDOC) 