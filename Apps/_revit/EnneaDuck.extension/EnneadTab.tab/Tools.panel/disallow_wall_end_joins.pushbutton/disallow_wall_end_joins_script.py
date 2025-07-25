#!/usr/bin/python
# -*- coding: utf-8 -*-

__doc__ = "Disallows wall end joins by wall type. This tool allows you to select specific wall types and disable their end joins, preventing automatic joining behavior at wall endpoints."
__title__ = "Disallow Wall\nEnd Joins"

import proDUCKtion # pyright: ignore 
proDUCKtion.validify()

from EnneadTab import ERROR_HANDLE, LOG, NOTIFICATION
from EnneadTab.REVIT import REVIT_APPLICATION, REVIT_SELECTION
from Autodesk.Revit import DB # pyright: ignore
from pyrevit import forms 

UIDOC = REVIT_APPLICATION.get_uidoc()
DOC = REVIT_APPLICATION.get_doc()


def get_wall_type_name(wall_type):
    """Helper function to get wall type name safely."""
    try:
        return wall_type.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM).AsString()
    except:
        return "Unknown Wall Type"


def get_all_wall_types(doc):
    """Helper function to get all wall types from document."""
    return DB.FilteredElementCollector(doc).OfClass(DB.WallType).ToElements()


def pick_wall_types():
    """Let user pick wall types from UI."""
    wall_types = get_all_wall_types(DOC)
    
    if not wall_types:
        NOTIFICATION.messenger("No wall types found in the document.")
        return []
    
    
    # Create selection options using TemplateListItem
    class WallTypeOption(forms.TemplateListItem):
        @property
        def name(self):
            try:
                if hasattr(self.item, "Kind"):
                    wall_kind = self.item.Kind
                    if wall_kind == DB.WallKind.Basic:
                        wall_kind_str = "Basic"
                    elif wall_kind == DB.WallKind.Curtain:
                        wall_kind_str = "Curtain"
                    elif wall_kind == DB.WallKind.Stacked:
                        wall_kind_str = "Stacked"
                    elif wall_kind == DB.WallKind.Unknown:
                        wall_kind_str = "Unknown"
                    else:
                        wall_kind_str = str(wall_kind)
                else:
                    wall_kind_str = "In-Place"
                return "[{}]{}".format(wall_kind_str, get_wall_type_name(self.item))
            except:
                return "[Unknown]{}".format(get_wall_type_name(self.item))
    
    wall_type_options = [WallTypeOption(wt) for wt in wall_types]
    # Sort wall types by name
    wall_type_options = sorted(wall_type_options, key=lambda x: x.name)
    
    # Let user select wall types
    selected_wall_types = forms.SelectFromList.show(
        wall_type_options,
        title="Select Wall Types to Disallow End Joins",
        multiselect=True,
        button_name="Select Wall Types"
    )
    
    if not selected_wall_types:
        NOTIFICATION.messenger("No wall types selected.")
        return []
    
    return selected_wall_types


def get_walls_by_type(doc, wall_types):
    """Get all walls of the specified wall types."""
    if not wall_types:
        return []
    
    all_walls = DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Walls).WhereElementIsNotElementType().ToElements()
    
    # Debug information
    print("Found {} total walls in document".format(len(all_walls)))
    print("Looking for walls of types: {}".format(", ".join([get_wall_type_name(wt) for wt in wall_types])))
    
    # Create a set of selected wall type IDs for faster comparison
    selected_type_ids = {wt.Id for wt in wall_types}
    selected_type_names = [get_wall_type_name(wt) for wt in wall_types]
    
    print("Selected wall type names: {}".format(selected_type_names))
    print("Selected wall type IDs: {}".format([str(wt.Id) for wt in wall_types]))
    
    # Filter walls by wall type
    target_walls = []
    
    for wall in all_walls:
        wall_type_name = get_wall_type_name(wall.WallType)
        wall_type_id = wall.WallType.Id
        
        # Check if this wall's type ID matches any selected type ID
        if wall_type_id in selected_type_ids:
            target_walls.append(wall)
            print("✓ Found wall of type: {} (ID: {})".format(wall_type_name, wall_type_id))
        else:
            # Debug: show some wall types that don't match
            if len(target_walls) < 5:  # Only show first few non-matches
                print("✗ Wall type not selected: {} (ID: {})".format(wall_type_name, wall_type_id))
    
    print("Found {} walls matching selected types".format(len(target_walls)))
    return target_walls


@LOG.log(__file__, __title__)
@ERROR_HANDLE.try_catch_error()
def set_wall_end_joins(walls):
    """Set wall end joins for the given walls."""
    if not walls:
        NOTIFICATION.messenger("No walls to process.")
        return
    
    t = DB.Transaction(DOC, __title__)
    t.Start()
    
    processed_count = 0
    failed_count = 0
    failed_names = []
    
    print("Processing {} walls to disallow end joins...".format(len(walls)))
    
    for wall in walls:
        try:
            # Debug: Check wall properties before processing
            print("Processing wall: {} (ID: {})".format(get_wall_type_name(wall.WallType), wall.Id))
            print("  - Wall curve length: {}".format(wall.Location.Curve.GetEndPoint(1).DistanceTo(wall.Location.Curve.GetEndPoint(0))))
            print("  - Wall height: {}".format(wall.get_Parameter(DB.BuiltInParameter.WALL_USER_HEIGHT_PARAM).AsDouble()))
            
            # Disallow end joins for both ends of the wall (0 = start, 1 = end)
            DB.WallUtils.DisallowWallJoinAtEnd(wall, 0)  # Start end
            print("  ✓ Disallowed start end")
            DB.WallUtils.DisallowWallJoinAtEnd(wall, 1)  # End end
            print("  ✓ Disallowed end end")
            processed_count += 1
        except Exception as e:
            failed_count += 1
            wall_name = get_wall_type_name(wall.WallType)
            failed_names.append(wall_name)
            print("✗ Failed to disallow end joins for wall: {} (ID: {})".format(wall_name, wall.Id))
            print("  Error: {}".format(str(e)))
            continue
    
    t.Commit()
    
    # Provide comprehensive feedback
    message = "Successfully processed {} walls to disallow end joins.".format(processed_count)
    if failed_count > 0:
        message += " Failed: {} ({}).".format(failed_count, ", ".join(failed_names[:3]) + ("..." if len(failed_names) > 3 else ""))
    
    print(message)


@LOG.log(__file__, __title__)
@ERROR_HANDLE.try_catch_error()
def disallow_wall_end_join(doc, uidoc):
    """
    Main entry function for disallowing wall end joins.
    Checks for selections and provides appropriate behavior:
    - If walls are selected: process those wall types
    - If no selection: show UI for wall type selection
    """
    selection = uidoc.Selection.GetElementIds()
    walls = []
    
    if selection:
        # Check if any of the selected elements are walls
        for element_id in selection:
            element = doc.GetElement(element_id)
            if isinstance(element, DB.Wall):
                walls.append(element)
    
    # If no walls found in selection, let user pick wall types
    if not walls:
        wall_types = pick_wall_types()
        if wall_types:  # Only proceed if user selected wall types
            NOTIFICATION.messenger("User selected {} wall types".format(len(wall_types)))
            walls = get_walls_by_type(doc, wall_types)
        else:
            NOTIFICATION.messenger("No wall types selected by user")
    
    # If still no walls, show error message
    if not walls:
        NOTIFICATION.messenger("No walls found. Please select walls or choose wall types that have walls in the model.")
        return
    
    set_wall_end_joins(walls)


################## main code below #####################
if __name__ == "__main__":
    disallow_wall_end_join(DOC, UIDOC) 