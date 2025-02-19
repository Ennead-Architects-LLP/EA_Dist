import os
import sys
root_folder = os.path.abspath((os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(root_folder)

import NOTIFICATION
import DATA_FILE
import FOLDER
import ENVIRONMENT
try:
    from Autodesk.Revit import DB # pyright: ignore
    from Autodesk.Revit import UI # pyright: ignore
    from pyrevit import forms
    import REVIT_PARAMETER
except:
    pass

PROJECT_DATA_PREFIX = "ProjectData_"
PROJECT_DATA_PARA_NAME = "EnneadTab_Data"


def is_setup_project_data_para_exist(doc):
    """Check if the EnneadTab_Data parameter exists in project information.
    
    Args:
        doc: Current Revit document
        
    Returns:
        bool: True if parameter exists, False otherwise
    """
    para = get_project_info_para_by_name(doc, PROJECT_DATA_PARA_NAME)
    if para:
        return True
    return False

def get_project_info_para_by_name(doc, para_name):
    """Retrieve a parameter from project information by its name.
    
    Args:
        doc: Current Revit document
        para_name: Name of the parameter to find
        
    Returns:
        Parameter: Found parameter object or None if not found
    """
    proj_info = doc.ProjectInformation
    for para in proj_info.Parameters:
        if para.Definition.Name == para_name:
            return para
    return None



def get_project_data_name(doc):
    """Get or create the project data identifier parameter.
    
    Creates the shared parameter if it doesn't exist and initializes it
    with the document title.
    
    Args:
        doc: Current Revit document
        
    Returns:
        str: Value of the project data parameter
    """
    # Check if parameter exists using the helper function
    if not is_setup_project_data_para_exist(doc):
        definition = REVIT_PARAMETER.get_shared_para_definition_in_txt_file_by_name(doc, PROJECT_DATA_PARA_NAME)
        if not definition:
            definition = REVIT_PARAMETER.create_shared_parameter_in_txt_file(doc, PROJECT_DATA_PARA_NAME, DB.SpecTypeId.String.Text)
        REVIT_PARAMETER.add_shared_parameter_to_project_doc(doc, 
                                                        definition, 
                                                        "Data", 
                                                        [DB.Category.GetCategory(doc,DB.BuiltInCategory.OST_ProjectInformation)])

        para = get_project_info_para_by_name(doc, PROJECT_DATA_PARA_NAME)
        para.Set(doc.Title)  # Set initial value to document title

    # Get the parameter value
    return get_project_info_para_by_name(doc, PROJECT_DATA_PARA_NAME).AsString()

def get_project_data_file(doc):
    """Generate the project data file name based on project identifier.
    
    Args:
        doc: Current Revit document
        
    Returns:
        str: Full filename for project data storage
    """
    project_data_name = get_project_data_name(doc)
    return "{}{}.sexyDuck".format(PROJECT_DATA_PREFIX, project_data_name)


def mark_doc_to_project_data_file(doc):
    """Record current document in the list of documents using this project data.
    
    Args:
        doc: Current Revit document
    """
    data = get_revit_project_data(doc)
    if "docs_attaching" not in data:
        data["docs_attaching"] = []
    data["docs_attaching"].append(doc.Title)
    set_revit_project_data(doc, data)

def reattach_project_data(doc):
    """Reattach project data from an existing setup file.
    
    Allows user to select from available project data files in the shared
    drive and updates the current document's project data reference.
    
    Args:
        doc: Current Revit document
    """
    # Print current project data file
    current_data_name = get_project_data_name(doc)
    print("Current project data file: {}".format(current_data_name))

    # Get all project data files from shared dump folder
    data_files = [f for f in os.listdir(FOLDER.SHARED_DUMP_FOLDER) if f.startswith(PROJECT_DATA_PREFIX) and f.endswith(".sexyDuck")]
    
    # Extract XXX parts for display (without extension)
    display_options = [f.replace(PROJECT_DATA_PREFIX, "").replace(".sexyDuck", "") for f in data_files]
    
    if not display_options:
        NOTIFICATION.messenger("No project data files found in L drive.")
        return
    
    # Let user pick from the list
    selected = forms.SelectFromList.show(
        display_options,
        multiselect=False,
        title="Select Project Data File to Attach",
        button_name="Select"
    )
        
    if not selected:
        return
    
    # Update project data file reference
    try:
        get_project_info_para_by_name(doc, PROJECT_DATA_PARA_NAME).Set("{}".format(selected))
        mark_doc_to_project_data_file(doc)
        NOTIFICATION.messenger("Successfully reattached project data.")
    except Exception as e:
        NOTIFICATION.messenger("Failed to reattach project data: {}".format(str(e)))


def get_revit_project_data(doc):
    """Retrieve project data from shared storage.
    
    Args:
        doc: Current Revit document
        
    Returns:
        dict: Project data dictionary from storage
    """
    ENVIRONMENT.alert_l_drive_not_available()
    return DATA_FILE.get_data(get_project_data_file(doc), is_local=False)


def set_revit_project_data(doc, data):
    """Save project data to shared storage.
    
    Args:
        doc: Current Revit document
        data: Dictionary containing project data to save
    """
    DATA_FILE.set_data(data, get_project_data_file(doc), is_local=False)