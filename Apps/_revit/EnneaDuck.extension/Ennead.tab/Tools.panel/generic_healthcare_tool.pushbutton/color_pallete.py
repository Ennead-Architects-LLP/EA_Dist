from EnneadTab import NOTIFICATION
from EnneadTab.REVIT import REVIT_COLOR_SCHEME, REVIT_FOLDER
from pyrevit import forms

def update_color_pallete(doc):


    print ("excel path has been defined")
    NOTIFICATION.messenger(main_text="Select the excel file that contains the color pallete")
    excel_path = forms.pick_file(title="Select the excel file", filter="Excel Files (*.xls)|*.xls")
    if not excel_path:
        NOTIFICATION.messenger(main_text="No excel file selected")
        return

    naming_map = {"department_color_map":"Primary_Department Category",
                  "program_color_map":"Primary_Department Program Type"}


    is_remove_bad = REVIT_FORMS.dialogue(main_text="Do you want to remove the bad color?", button_name="Remove Bad Color")

    print ("color sceme name has been defined")

    REVIT_COLOR_SCHEME.load_color_template(doc, naming_map, excel_path, is_remove_bad)
