from EnneadTab import NOTIFICATION
from EnneadTab.REVIT import REVIT_COLOR_SCHEME, REVIT_FORMS
from pyrevit import forms

def update_color_pallete(doc):


    NOTIFICATION.messenger(main_text="Select the excel file that contains the color pallete")
    excel_path = forms.pick_file(title="Select the excel file", files_filter="Excel Files (*.xls)|*.xls")
    if not excel_path:
        NOTIFICATION.messenger(main_text="No excel file selected")
        return



    department_color_scheme_name = REVIT_COLOR_SCHEME.pick_color_scheme(doc, title="Select the [DEPARTMENT] color scheme", button_name="Select [DEPARTMENT] color scheme")
    if not department_color_scheme_name:
        NOTIFICATION.messenger(main_text="No [DEPARTMENT] color scheme selected")
        return
    program_color_scheme_name = REVIT_COLOR_SCHEME.pick_color_scheme(doc, title="Select the [PROGRAM] color scheme", button_name="Select [PROGRAM] color scheme")     
    if not program_color_scheme_name:
        NOTIFICATION.messenger(main_text="No [PROGRAM] color scheme selected")
        return

    naming_map = {"department_color_map":department_color_scheme_name,
                  "program_color_map":program_color_scheme_name}

    options = ["Remove Unused Color", "Keep Unused Color"]
    select_option = REVIT_FORMS.dialogue(options = options, main_text="Do you want to remove the unused color?")
    if select_option == options[0]:
        is_remove_unused = True
    else:
        is_remove_unused = False
    

    REVIT_COLOR_SCHEME.load_color_template(doc, naming_map, excel_path, is_remove_unused)