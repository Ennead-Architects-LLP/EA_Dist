__doc__ = "Sen Zhang has not writed documentation for this tool, but he should!"
__title__ = "Query Main Excel"

import proDUCKtion # pyright: ignore 
proDUCKtion.validify()
import os

from EnneadTab import ERROR_HANDLE, LOG, EXCEL
# from EnneadTab.REVIT import REVIT_APPLICATION
from Autodesk.Revit import DB # pyright: ignore 

# UIDOC = REVIT_APPLICATION.get_uidoc()
# DOC = REVIT_APPLICATION.get_doc()




url = "https://acc.autodesk.com/docs/files/projects/4c18861d-816c-4b78-935f-164aea2369fd?folderUrn=urn%3Aadsk.wipprod%3Afs.folder%3Aco.ZmvIgFreSWOCIMXW3JZBkQ&entityId=urn%3Aadsk.wipprod%3Adm.lineage%3AVtUKUAYpTy-t-51ttuWCzA&viewModel=detail&moduleId=folders&activeCell=%27EA%20Benchmarking%20DGSF%20Tracker%27!C74&wdinitialsession=12138c1a-b4a7-44b3-81ce-c5932ae998fb&wdrldsc=4&wdrldc=1&wdrldr=AccessTokenExpiredSilentRefreshDisabled"

@LOG.log(__file__, __title__)
@ERROR_HANDLE.try_catch_error()
def query_main_excel():
    # data = EXCEL.read_data_from_excel(url, "EA Benchmarking DGSF Tracker", return_dict=True)
    # print(data)

    # # t = DB.Transaction(DOC, __title__)
    # # t.Start()
    # # pass
    # # t.Commit()
    source_excel = "{}\\DC\\ACCDocs\\Ennead Architects LLP\\2151_NYULI\\Project Files\\00_EA-EC Teams Files\\4_Programming\\_Public Shared\\archive\\Web Portal Only_ACTIVE.NYULI_Program_EA.EC.xlsx".format(os.getenv("USERPROFILE"))
    # source_excel = FOLDER.get_EA_dump_folder_file("temptemp.xlsx")
    # NOTIFICATION.duck_pop(main_text="using testing file for now.")
    data = EXCEL.read_data_from_excel(source_excel, 
                                      worksheet="EA Benchmarking DGSF Tracker", 
                                      return_dict=True,
                                      headless=True) # if have permission lock---> set it as always availble in this PC from desktop connecter.


    AbstractDepartment.data = data

    section_list = [
        "A - EMERGENCY DEPARTMENT",
        "B - DIAGNOSTIC AND TREATMENT",
        "C - INPATIENT CARE",
        "D - CLINICAL SUPPORT",
        "E - PUBLIC SUPPORT",
        "F - ADMINISTRATION AND STAFF SUPPORT",
        "G - BUILDING SUPPORT"
        
        
        ]
    current_section_title = None
    for pointer in sorted(data.keys()):

        row, column = pointer
        value = data[pointer]["value"]
        print (row, column, value)
        

    


class AbstractDepartment:
    raw_data = {}
    def __init__(self, begin_row, end_row, secondary_data_column):
        self.name = self.__class__.__name__

        self.secondary_data = {}
        for pointer in sorted(self.raw_data.keys()):
            row, column = pointer
            if begin_row <= row <= end_row and column == secondary_data_column:
                value = self.raw_data[pointer]["value"]
                if value != "":
                    self.secondary_data[(row, column)] = value

class EmergencyDepartment(AbstractDepartment):
    pass

class DiagnositicAndTreatment(AbstractDepartment):
    pass

class InpatientCare(AbstractDepartment):
    pass

class ClinicalSupport(AbstractDepartment):
    pass

class PublicSupport(AbstractDepartment):
    pass

class AdministrationAndStaffSupport(AbstractDepartment):
    pass

class BuildingSupport(AbstractDepartment):
    pass

################## main code below #####################
if __name__ == "__main__":
    query_main_excel()







