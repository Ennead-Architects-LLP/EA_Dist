# -*- coding: utf-8 -*-

from EnneadTab import NOTIFICATION
import REVIT_APPLICATION

try:

    from Autodesk.Revit import DB # pyright: ignore
    from Autodesk.Revit import UI # pyright: ignore
    UIDOC = REVIT_APPLICATION.get_uidoc() 
    DOC = REVIT_APPLICATION.get_doc()
    
except:
    globals()["UIDOC"] = object()
    globals()["DOC"] = object()


def get_tagged_element(tag, doc):
    """Get the element that a tag is referencing"""
    try:
        # Try getting Host property first (for family instance tags)
        if hasattr(tag, "Host") and tag.Host:

            return tag.Host
        
        if hasattr(tag, "TaggedLocalElementId"):
            host = doc.GetElement(tag.TaggedLocalElementId)
            if host:
               
                return host

        if hasattr(tag, "TaggedElementId "):
            host = doc.GetElement(tag.TaggedElementId )
            if host:
       
                return host

        # Try GetTaggedLocalElement next (for other element tags)
        if hasattr(tag, "GetTaggedLocalElement"):
            host = tag.GetTaggedLocalElement()
            if host:

                return host
                
        # Last resort - try getting via tagged reference
        if hasattr(tag, "GetTaggedReference"):
            host_ref = tag.GetTaggedReference() 
            if host_ref:
                host = doc.GetElement(host_ref.ElementId)
                if host:
                 
                    return host
                
       
        return None
        
    except Exception as e:
       
        return None


def purge_tags(bad_host_family_names, tag_category, doc = DOC):
    """get all the tags from project, if its host's name is in the list, delete it"""

    all_tags = DB.FilteredElementCollector(doc).OfCategory(tag_category).WhereElementIsNotElementType().ToElements()
    for tag in all_tags:
        host = get_tagged_element(tag, doc)


        if host and host.FamilyName in bad_host_family_names:
            doc.Delete(tag.Id)



def retag_by_family_type(tag_family_name, tag_type_name, host_family_name, host_type_name, doc = DOC):
    """retag all the tags with the given family and type name"""
    
    all_tags = DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Tags).ToElements()
    
    # Get the tag type element id first
    tag_type = DB.FilteredElementCollector(doc)\
                .OfClass(DB.FamilySymbol)\
                .Where(lambda x: x.FamilyName == tag_family_name and x.Name == tag_type_name)\
                .FirstElement()
    
    if tag_type is None:
        print("Quack! Couldn't find that tag type. Did it fly south for the winter?")
        return
        
    for tag in all_tags:
        host = get_tagged_element(tag, doc)
        if host and host.FamilyName == host_family_name and host.TypeName == host_type_name:
            try:
                # Here's the correct way to change the tag type
                tag.ChangeTypeId(tag_type.Id)
            except Exception as e:
                print("Oops! This tag is being rebellious: {}".format(e))
                # Maybe it's having an identity crisis?
                continue
