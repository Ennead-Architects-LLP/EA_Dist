#!/usr/bin/python
# -*- coding: utf-8 -*-

__doc__ = """Batch upgrade Revit family files to the current Revit version.

This tool processes all .rfa files in the EnneadTab family folder and upgrades them to the current 
Revit version by opening and resaving them. Upgraded families are saved in version-specific 
subfolders to preserve originals. 

Features:
- Automatic error handling with pyrevit ErrorSwallower
- Progress tracking and detailed logging
- Version-specific output folders
- Comprehensive error reporting
- Graceful handling of problematic files
- User confirmation dialog with cancel option

The tool will continue processing even if individual families encounter warnings or minor errors,
providing a summary of any issues at the end.
"""
__title__ = "Upgrade\nFamilies"
__context__ = "zero-doc"

import os
import time

import proDUCKtion # pyright: ignore 
proDUCKtion.validify()

from EnneadTab import ERROR_HANDLE, LOG, ENVIRONMENT, TIME
from EnneadTab.REVIT import REVIT_APPLICATION, REVIT_FORMS
from Autodesk.Revit import DB # pyright: ignore 
from Autodesk.Revit.DB import ModelPathUtils
from pyrevit.revit import ErrorSwallower # pyright: ignore

UIDOC = REVIT_APPLICATION.get_uidoc()
DOC = REVIT_APPLICATION.get_doc()


class FamilyUpgradeResult(object):
    """Container for family upgrade operation results."""
    
    def __init__(self, family_name, success, error_message=None, warnings=None):
        self.family_name = family_name
        self.success = success
        self.error_message = error_message
        self.warnings = warnings or []
    
    def __str__(self):
        if self.success:
            return "SUCCESS: {}".format(self.family_name)
        else:
            return "FAILED: {} - {}".format(self.family_name, self.error_message)


class FamilyUpgradeProcessor(object):
    """Handles the processing of individual family files."""
    
    def __init__(self, app):
        self.app = app
        self.processed_docs = []
    
    def process_family(self, file_path, output_path):
        """Process a single family file and return result."""
        family_name = os.path.basename(file_path)
        warnings = []
        
        try:
            # Open family with ErrorSwallower
            open_options = DB.OpenOptions()
            model_path = ModelPathUtils.ConvertUserVisiblePathToModelPath(file_path)
            
            with ErrorSwallower() as swallower:
                family_doc = self.app.OpenDocumentFile(model_path, open_options)
                
                # Check for swallowed errors during opening
                errors = swallower.get_swallowed_errors()
                if errors:
                    warnings.append("Opening warnings: {}".format(errors))
            
            # Save as with new name using ErrorSwallower
            save_options = DB.SaveAsOptions()
            save_options.OverwriteExistingFile = True
            
            with ErrorSwallower() as swallower:
                family_doc.SaveAs(output_path, save_options)
                
                # Check for swallowed errors during saving
                errors = swallower.get_swallowed_errors()
                if errors:
                    warnings.append("Saving warnings: {}".format(errors))
            
            # Store the document for later closing
            self.processed_docs.append(family_doc)
            
            return FamilyUpgradeResult(family_name, True, warnings=warnings)
            
        except Exception as e:
            return FamilyUpgradeResult(family_name, False, str(e), warnings)
    
    def close_all_documents(self):
        """Close all processed family documents."""
        for i, family_doc in enumerate(self.processed_docs, 1):
            try:
                family_doc.Close(False)
                print("Closed document {}/{}".format(i, len(self.processed_docs)))
            except Exception as e:
                print("Error closing family document: {}".format(str(e)))


class FamilyUpgradeManager(object):
    """Main manager class for family upgrade operations."""
    
    def __init__(self):
        self.app = REVIT_APPLICATION.get_app()
        self.processor = FamilyUpgradeProcessor(self.app)
        self.results = []
        self.start_time = None
    
    def get_family_folder(self):
        """Return the path to the folder containing family files."""
        return os.path.join(ENVIRONMENT.DOCUMENT_FOLDER, "revit")
    
    def get_family_files(self, folder_path):
        """Get all eligible family files from the folder."""
        if not os.path.exists(folder_path):
            print("The family folder does not exist: {}".format(folder_path))
            return []
        
        family_files = [f for f in os.listdir(folder_path) if f.endswith(".rfa")]
        
        if not family_files:
            print("No eligible family files found in the folder.")
            return []
        
        return family_files
    
    def create_version_folder(self, base_folder):
        """Create version-specific subfolder for output."""
        version_folder = os.path.join(base_folder, str(REVIT_APPLICATION.get_revit_version()))
        if not os.path.exists(version_folder):
            os.makedirs(version_folder)
        return version_folder
    
    def show_warning_dialog(self):
        """Show warning dialog and return user's choice."""
        options = ["Yes, Continue", "Cancel"]
        warning_result = REVIT_FORMS.dialogue(
            main_text="This upgrade process will likely crash Revit after upgrade complete, but it is totally fine to happen.",
            sub_text="Make sure you understand this before continue. Still continue?",
            title="EnneadTab - Family Upgrade Warning",
            options=options,
            icon="warning"
        )
        
        return warning_result == "Yes, Continue"
    
    def process_families(self, family_files, base_folder, version_folder):
        """Process all family files and collect results."""
        total_families = len(family_files)
        print("Starting to process {} family files...".format(total_families))
        
        for index, family_file in enumerate(family_files, 1):
            print("Processing family {}/{}: {}".format(index, total_families, family_file))
            
            file_path = os.path.join(base_folder, family_file)
            output_path = os.path.join(version_folder, family_file)
            
            result = self.processor.process_family(file_path, output_path)
            self.results.append(result)
            
            if result.success:
                print("Successfully processed: {}".format(family_file))
            else:
                print("Error processing family '{}': {}".format(family_file, result.error_message))
    
    def print_summary(self):
        """Print comprehensive summary of the upgrade operation."""
        successful = [r for r in self.results if r.success]
        failed = [r for r in self.results if not r.success]
        
        print("\n" + "="*60)
        print("UPGRADE SUMMARY")
        print("="*60)
        print("Total files processed: {}".format(len(self.results)))
        print("Successfully upgraded: {}".format(len(successful)))
        print("Failed: {}".format(len(failed)))
        
        if self.start_time:
            elapsed_time = time.time() - self.start_time
            print("Total time: {}".format(TIME.get_readable_time(elapsed_time)))
        
        # Report any warnings
        all_warnings = []
        for result in self.results:
            all_warnings.extend(result.warnings)
        
        if all_warnings:
            print("\n" + "="*60)
            print("WARNINGS SUMMARY")
            print("="*60)
            for warning in all_warnings:
                print(warning)
        
        # Report failures
        if failed:
            print("\n" + "="*60)
            print("FAILED FILES")
            print("="*60)
            for result in failed:
                print(result)
    
    def run(self):
        """Main execution method."""
        # Show warning dialog
        if not self.show_warning_dialog():
            print("Family upgrade cancelled by user.")
            return
        
        # Get family folder and files
        folder_path = self.get_family_folder()
        family_files = self.get_family_files(folder_path)
        
        if not family_files:
            return
        
        print("Found {} family files to upgrade.".format(len(family_files)))
        
        # Create version folder
        version_folder = self.create_version_folder(folder_path)
        
        # Start processing
        self.start_time = time.time()
        
        try:
            self.process_families(family_files, folder_path, version_folder)
        finally:
            # Always close documents
            self.processor.close_all_documents()
        
        # Print summary
        self.print_summary()
        
        # Close Revit app
        REVIT_APPLICATION.close_revit_app()


@LOG.log(__file__, __title__)
@ERROR_HANDLE.try_catch_error()
def upgrade_families(doc):
    """Main function to upgrade family files."""
    manager = FamilyUpgradeManager()
    manager.run()


################## main code below #####################
if __name__ == "__main__":
    upgrade_families(DOC)







