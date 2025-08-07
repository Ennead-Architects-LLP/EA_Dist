"""
Template Data Collector Module

This module handles all data collection operations for view templates,
including category overrides, visibility settings, worksets, parameters, and filters.
"""

import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitServices')
import Autodesk.Revit.DB as DB

from pyrevit import forms
from pyrevit import script

from EnneadTab import ERROR_HANDLE
from EnneadTab.REVIT import REVIT_CATEGORY


class TemplateDataCollector:
    """
    Handles data collection from view templates.
    
    This class is responsible for extracting all relevant data from view templates
    including category overrides, visibility settings, worksets, parameters, and filters.
    """
    
    def __init__(self, doc):
        """
        Initialize the data collector.
        
        Args:
            doc: The Revit document
        """
        self.doc = doc
        self.categories = self._get_sorted_categories()
        # Set iteration limits to prevent infinite loops
        self.max_categories = 1000
        self.max_subcategories = 5000
        self.max_worksets = 100
        self.max_filters = 500
    
    def _get_sorted_categories(self):
        """
        Get all categories and subcategories sorted alphabetically using RevitCategory class.
        
        Returns:
            list: Sorted list of RevitCategory objects
        """
        categories = []
        category_count = 0
        subcategory_count = 0
        
        try:
            # Get all categories with iteration limit
            for category in self.doc.Settings.Categories:
                category_count += 1
                if category_count > self.max_categories:
                    ERROR_HANDLE.print_note("Category iteration limit reached ({}), stopping.".format(self.max_categories))
                    break
                
                try:
                    if category and category.AllowsBoundParameters:
                        # Add main category using RevitCategory wrapper
                        revit_category = REVIT_CATEGORY.RevitCategory(category)
                        categories.append(revit_category)
                        
                        # Add subcategories with limit
                        if hasattr(category, 'SubCategories'):
                            for subcategory in category.SubCategories:
                                subcategory_count += 1
                                if subcategory_count > self.max_subcategories:
                                    ERROR_HANDLE.print_note("Subcategory iteration limit reached ({}), stopping.".format(self.max_subcategories))
                                    break
                                
                                try:
                                    if subcategory and subcategory.AllowsBoundParameters:
                                        revit_subcategory = REVIT_CATEGORY.RevitCategory(subcategory)
                                        categories.append(revit_subcategory)
                                except Exception as e:
                                    ERROR_HANDLE.print_note("Error processing subcategory: {}".format(str(e)))
                                    continue
                except Exception as e:
                    ERROR_HANDLE.print_note("Error processing category: {}".format(str(e)))
                    continue
                    
        except Exception as e:
            ERROR_HANDLE.print_note("Error getting categories: {}".format(str(e)))
            return []
        
        # Sort by pretty name
        try:
            return sorted(categories, key=lambda x: x.pretty_name)
        except Exception as e:
            ERROR_HANDLE.print_note("Error sorting categories: {}".format(str(e)))
            return categories
    
    def get_category_overrides(self, template):
        """
        Extract category override settings from a template.
        
        Improved error handling:
        - Uses RevitCategory class for better category management
        - Checks if category allows bound parameters before attempting override
        - Uses ERROR_HANDLE.print_note for detailed error reporting
        - Provides summary of skipped categories
        - Uses explicit exception handling instead of silent try-catch
        - Added iteration limits to prevent infinite loops
        
        Args:
            template: The view template to analyze
            
        Returns:
            dict: Category override settings with readable pattern names
        """
        overrides = {}
        skipped_categories = []
        processed_count = 0
        
        for revit_category in self.categories:
            processed_count += 1
            if processed_count > self.max_categories:
                ERROR_HANDLE.print_note("Category override processing limit reached, stopping.")
                break
                
            # Pre-check if category allows bound parameters
            try:
                if not revit_category.category.AllowsBoundParameters:
                    continue
            except Exception as e:
                ERROR_HANDLE.print_note("Error checking category capabilities: {}".format(str(e)))
                continue
                
            try:
                override = template.GetCategoryOverrides(revit_category.category.Id)
                if override:
                    overrides[revit_category.pretty_name] = self._extract_override_details(override)
            except Exception as e:
                # Log specific error for debugging
                error_msg = "Failed to get override for category '{}': {}".format(revit_category.pretty_name, str(e))
                skipped_categories.append(error_msg)
                ERROR_HANDLE.print_note(error_msg)
                continue
                
        # Log summary of skipped categories if any
        if skipped_categories:
            summary_msg = "Skipped {} categories during override extraction: {}".format(
                len(skipped_categories), ", ".join(skipped_categories[:5])  # Show first 5
            )
            ERROR_HANDLE.print_note(summary_msg)
            
        return overrides
    
    def _extract_override_details(self, override):
        """
        Extract detailed override information from OverrideGraphicSettings.
        
        Args:
            override: OverrideGraphicSettings object
            
        Returns:
            dict: Detailed override information
        """
        details = {}
        
        try:
            # Halftone
            details['halftone'] = override.Halftone
            
            # Line weight
            details['line_weight'] = override.LineWeight
            
            # Line color
            line_color = override.LineColor
            details['line_color'] = self._format_color(line_color)
            
            # Line pattern
            details['line_pattern'] = self._get_pattern_name(override.LinePatternId)
            
            # Cut line weight
            details['cut_line_weight'] = override.CutLineWeight
            
            # Cut line color
            cut_line_color = override.CutLineColor
            details['cut_line_color'] = self._format_color(cut_line_color)
            
            # Cut line pattern
            details['cut_line_pattern'] = self._get_pattern_name(override.CutLinePatternId)
            
            # Cut fill pattern
            details['cut_fill_pattern'] = self._get_pattern_name(override.CutFillPatternId)
            
            # Cut fill color
            cut_fill_color = override.CutFillColor
            details['cut_fill_color'] = self._format_color(cut_fill_color)
            
            # Projection fill pattern
            details['projection_fill_pattern'] = self._get_pattern_name(override.ProjectionFillPatternId)
            
            # Projection fill color
            projection_fill_color = override.ProjectionFillColor
            details['projection_fill_color'] = self._format_color(projection_fill_color)
            
            # Transparency
            details['transparency'] = override.Transparency
            
        except Exception as e:
            ERROR_HANDLE.print_note("Error extracting override details: {}".format(str(e)))
            # Return minimal details if extraction fails
            details = {'error': 'Failed to extract override details'}
            
        return details
    
    def _get_pattern_name(self, pattern_id):
        """
        Get readable pattern name from pattern ID.
        
        Args:
            pattern_id: The ElementId of the pattern
            
        Returns:
            str: Pattern name or "Default" if not found
        """
        if pattern_id == DB.ElementId.InvalidElementId:
            return "Default"
        
        try:
            pattern = self.doc.GetElement(pattern_id)
            if pattern:
                return pattern.Name
            else:
                ERROR_HANDLE.print_note("Pattern element not found for ID: {}".format(pattern_id))
                return "Default"
        except Exception as e:
            ERROR_HANDLE.print_note("Failed to get pattern name for ID {}: {}".format(pattern_id, str(e)))
            return "Default"
    
    def _format_color(self, color):
        """
        Format color as RGB string.
        
        Args:
            color: Color object
            
        Returns:
            str: RGB color string
        """
        if color:
            return "RGB({}, {}, {})".format(color.Red, color.Green, color.Blue)
        return "Default"
    
    def get_category_visibility(self, template):
        """
        Get category visibility settings from template.
        
        Improved error handling:
        - Uses RevitCategory class for better category management
        - Checks if category allows bound parameters before attempting visibility check
        - Uses ERROR_HANDLE.print_note for detailed error reporting
        - Provides summary of skipped categories
        - Uses explicit exception handling instead of silent try-catch
        - Added iteration limits to prevent infinite loops
        
        Args:
            template: The view template to analyze
            
        Returns:
            dict: Category visibility settings (On/Off)
        """
        visibility = {}
        skipped_categories = []
        processed_count = 0
        
        for revit_category in self.categories:
            processed_count += 1
            if processed_count > self.max_categories:
                ERROR_HANDLE.print_note("Category visibility processing limit reached, stopping.")
                break
                
            # Pre-check if category allows bound parameters
            try:
                if not revit_category.category.AllowsBoundParameters:
                    continue
            except Exception as e:
                ERROR_HANDLE.print_note("Error checking category capabilities: {}".format(str(e)))
                continue
                
            try:
                is_hidden = template.GetCategoryHidden(revit_category.category.Id)
                visibility[revit_category.pretty_name] = "Off" if is_hidden else "On"
            except Exception as e:
                error_msg = "Failed to get visibility for category '{}': {}".format(revit_category.pretty_name, str(e))
                skipped_categories.append(error_msg)
                ERROR_HANDLE.print_note(error_msg)
                continue
                    
        # Log summary of skipped categories if any
        if skipped_categories:
            summary_msg = "Skipped {} categories during visibility extraction: {}".format(
                len(skipped_categories), ", ".join(skipped_categories[:5])
            )
            ERROR_HANDLE.print_note(summary_msg)
            
        return visibility
    
    def get_workset_visibility(self, template):
        """
        Get workset visibility settings from template.
        
        Improved error handling:
        - Uses FilteredWorksetCollector for proper workset collection
        - Uses ERROR_HANDLE.print_note for detailed error reporting
        - Provides summary of skipped worksets
        - Uses explicit exception handling instead of silent try-catch
        - Added iteration limits to prevent infinite loops
        
        Args:
            template: The view template to analyze
            
        Returns:
            dict: Workset visibility settings with readable text
        """
        worksets = {}
        skipped_worksets = []
        processed_count = 0
        
        try:
            workset_collector = DB.FilteredWorksetCollector(self.doc).OfKind(DB.WorksetKind.UserWorkset)
            
            for workset in workset_collector:
                processed_count += 1
                if processed_count > self.max_worksets:
                    ERROR_HANDLE.print_note("Workset processing limit reached, stopping.")
                    break
                    
                try:
                    visibility = template.GetWorksetVisibility(workset.Id)
                    worksets[workset.Name] = self._convert_visibility_to_text(visibility)
                except Exception as e:
                    error_msg = "Failed to get visibility for workset '{}': {}".format(workset.Name, str(e))
                    skipped_worksets.append(error_msg)
                    ERROR_HANDLE.print_note(error_msg)
                    continue
        except Exception as e:
            ERROR_HANDLE.print_note("Error getting worksets: {}".format(str(e)))
            return {}
                    
        # Log summary of skipped worksets if any
        if skipped_worksets:
            summary_msg = "Skipped {} worksets during visibility extraction: {}".format(
                len(skipped_worksets), ", ".join(skipped_worksets[:5])
            )
            ERROR_HANDLE.print_note(summary_msg)
            
        return worksets
    
    def _convert_visibility_to_text(self, visibility):
        """
        Convert workset visibility enum to readable text.
        
        Args:
            visibility: WorksetVisibility enum value
            
        Returns:
            str: Readable visibility text
        """
        if visibility == DB.WorksetVisibility.Visible:
            return "Visible"
        elif visibility == DB.WorksetVisibility.Hidden:
            return "Hidden"
        else:
            return "UseGlobalSetting"
    
    def get_view_parameters(self, template):
        """
        Get view parameters controlled by template.
        
        Args:
            template: The view template to analyze
            
        Returns:
            tuple: (controlled_params, uncontrolled_params)
        """
        controlled_params = []
        uncontrolled_params = []
        
        try:
            # Get non-controlled parameter IDs
            param_ids = template.GetNonControlledTemplateParameterIds()
            
            # Get all view parameters with iteration limit
            param_count = 0
            for param in template.Parameters:
                param_count += 1
                if param_count > 1000:  # Limit parameters to prevent infinite loops
                    ERROR_HANDLE.print_note("Parameter iteration limit reached, stopping.")
                    break
                    
                try:
                    if param.Id not in param_ids:
                        controlled_params.append(param.Definition.Name)
                    else:
                        uncontrolled_params.append(param.Definition.Name)
                except Exception as e:
                    ERROR_HANDLE.print_note("Error processing parameter: {}".format(str(e)))
                    continue
                    
        except Exception as e:
            ERROR_HANDLE.print_note("Error getting view parameters: {}".format(str(e)))
                
        return controlled_params, uncontrolled_params
    
    def get_filter_data(self, template):
        """
        Get filter usage and graphic override data.
        
        Improved error handling:
        - Uses ERROR_HANDLE.print_note for detailed error reporting
        - Provides summary of skipped filters
        - Uses explicit exception handling instead of silent try-catch
        - Added iteration limits to prevent infinite loops
        
        Args:
            template: The view template to analyze
            
        Returns:
            dict: Filter data with override settings
        """
        filters = {}
        skipped_filters = []
        processed_count = 0
        
        try:
            filter_ids = template.GetFilters()
            
            for filter_id in filter_ids:
                processed_count += 1
                if processed_count > self.max_filters:
                    ERROR_HANDLE.print_note("Filter processing limit reached, stopping.")
                    break
                    
                try:
                    filter_element = self.doc.GetElement(filter_id)
                    if filter_element:
                        override = template.GetFilterOverrides(filter_id)
                        filters[filter_element.Name] = self._extract_filter_override_details(override)
                except Exception as e:
                    error_msg = "Failed to get filter data for ID {}: {}".format(filter_id, str(e))
                    skipped_filters.append(error_msg)
                    ERROR_HANDLE.print_note(error_msg)
                    continue
        except Exception as e:
            ERROR_HANDLE.print_note("Error getting filters: {}".format(str(e)))
            return {}
                
        # Log summary of skipped filters if any
        if skipped_filters:
            summary_msg = "Skipped {} filters during extraction: {}".format(
                len(skipped_filters), ", ".join(skipped_filters[:5])
            )
            ERROR_HANDLE.print_note(summary_msg)
            
        return filters
    
    def _extract_filter_override_details(self, override):
        """
        Extract detailed filter override information.
        
        Args:
            override: The filter override object
            
        Returns:
            dict: Detailed filter override information
        """
        try:
            if not override:
                return None
                
            details = {}
            
            # Get visibility
            try:
                details['visibility'] = self._convert_visibility_to_text(override.GetVisibility())
            except:
                details['visibility'] = 'Unknown'
            
            # Get projection line weight
            try:
                details['projection_line_weight'] = override.GetProjectionLineWeight()
            except:
                details['projection_line_weight'] = None
            
            # Get projection line color
            try:
                details['projection_line_color'] = self._format_color(override.GetProjectionLineColor())
            except:
                details['projection_line_color'] = None
            
            # Get projection line pattern
            try:
                details['projection_line_pattern'] = self._get_pattern_name(override.GetProjectionLinePatternId())
            except:
                details['projection_line_pattern'] = None
            
            # Get cut line weight
            try:
                details['cut_line_weight'] = override.GetCutLineWeight()
            except:
                details['cut_line_weight'] = None
            
            # Get cut line color
            try:
                details['cut_line_color'] = self._format_color(override.GetCutLineColor())
            except:
                details['cut_line_color'] = None
            
            # Get cut line pattern
            try:
                details['cut_line_pattern'] = self._get_pattern_name(override.GetCutLinePatternId())
            except:
                details['cut_line_pattern'] = None
            
            # Get cut fill color
            try:
                details['cut_fill_color'] = self._format_color(override.GetCutFillColor())
            except:
                details['cut_fill_color'] = None
            
            # Get cut fill pattern
            try:
                details['cut_fill_pattern'] = self._get_pattern_name(override.GetCutFillPatternId())
            except:
                details['cut_fill_pattern'] = None
            
            # Get projection fill color
            try:
                details['projection_fill_color'] = self._format_color(override.GetProjectionFillColor())
            except:
                details['projection_fill_color'] = None
            
            # Get projection fill pattern
            try:
                details['projection_fill_pattern'] = self._get_pattern_name(override.GetProjectionFillPatternId())
            except:
                details['projection_fill_pattern'] = None
            
            # Get transparency
            try:
                details['transparency'] = override.GetTransparency()
            except:
                details['transparency'] = None
            
            # Get halftone
            try:
                details['halftone'] = override.IsHalftone()
            except:
                details['halftone'] = None
            
            return details
            
        except Exception as e:
            ERROR_HANDLE.print_note("Error extracting filter override details: {}".format(str(e)))
            return None

    def get_import_category_data(self, template):
        """
        Extract import category data from a template.
        
        Args:
            template: The view template
            
        Returns:
            dict: Import category data
        """
        import_categories = {}
        
        try:
            # Get import category overrides
            for category_id in template.GetNonControlledTemplateParameterIds():
                try:
                    category = self.doc.GetElement(category_id)
                    if category and hasattr(category, 'CategoryType'):
                        if category.CategoryType == DB.CategoryType.Imported:
                            category_name = category.Name
                            
                            # Get category override
                            try:
                                override = template.GetCategoryOverrides(category_id)
                                if override:
                                    import_categories[category_name] = self._extract_override_details(override)
                                else:
                                    import_categories[category_name] = "UNCONTROLLED"
                            except:
                                import_categories[category_name] = "UNCONTROLLED"
                except Exception as e:
                    ERROR_HANDLE.print_note("Error processing import category: {}".format(str(e)))
                    continue
                    
        except Exception as e:
            ERROR_HANDLE.print_note("Error getting import category data: {}".format(str(e)))
            
        return import_categories

    def get_revit_link_data(self, template):
        """
        Extract Revit link data from a template.
        
        Args:
            template: The view template
            
        Returns:
            dict: Revit link data
        """
        revit_links = {}
        
        try:
            # Get all Revit links in the document
            link_instances = DB.FilteredElementCollector(self.doc).OfClass(DB.RevitLinkInstance)
            
            for link_instance in link_instances:
                try:
                    link_name = link_instance.Name
                    
                    # Get link visibility
                    try:
                        visibility = template.GetRevitLinkVisibility(link_instance.Id)
                        revit_links[link_name] = {
                            'visibility': self._convert_visibility_to_text(visibility)
                        }
                    except:
                        revit_links[link_name] = {
                            'visibility': 'UNCONTROLLED'
                        }
                    
                    # Get link halftone
                    try:
                        revit_links[link_name]['halftone'] = template.IsRevitLinkDisplayedAsHalftone(link_instance.Id)
                    except:
                        revit_links[link_name]['halftone'] = None
                    
                    # Get link underlay
                    try:
                        revit_links[link_name]['underlay'] = template.IsRevitLinkDisplayedAsUnderlay(link_instance.Id)
                    except:
                        revit_links[link_name]['underlay'] = None
                    
                    # Get link display settings
                    try:
                        display_settings = template.GetRevitLinkDisplaySettings(link_instance.Id)
                        if display_settings:
                            revit_links[link_name]['display_settings'] = str(display_settings)
                        else:
                            revit_links[link_name]['display_settings'] = 'By Host View'
                    except:
                        revit_links[link_name]['display_settings'] = 'By Host View'
                        
                except Exception as e:
                    ERROR_HANDLE.print_note("Error processing Revit link {}: {}".format(link_name, str(e)))
                    continue
                    
        except Exception as e:
            ERROR_HANDLE.print_note("Error getting Revit link data: {}".format(str(e)))
            
        return revit_links

    def get_detail_level_data(self, template):
        """
        Extract detail level data from a template.
        
        Args:
            template: The view template
            
        Returns:
            dict: Detail level data
        """
        detail_levels = {}
        
        try:
            # Get detail level for categories
            for revit_category in self.categories:
                try:
                    category_id = revit_category.category.Id
                    category_name = revit_category.pretty_name
                    
                    # Get detail level override
                    try:
                        detail_level = template.GetDetailLevel(category_id)
                        if detail_level != DB.ViewDetailLevel.Undefined:
                            detail_levels[category_name] = str(detail_level)
                        else:
                            detail_levels[category_name] = "By View"
                    except:
                        detail_levels[category_name] = "By View"
                        
                except Exception as e:
                    ERROR_HANDLE.print_note("Error processing detail level for category {}: {}".format(category_name, str(e)))
                    continue
                    
        except Exception as e:
            ERROR_HANDLE.print_note("Error getting detail level data: {}".format(str(e)))
            
        return detail_levels

    def get_linetype_data(self, template):
        """
        Extract linetype data from a template.
        
        Args:
            template: The view template
            
        Returns:
            dict: Linetype data
        """
        linetypes = {}
        
        try:
            # Get all line patterns in the document
            line_patterns = DB.FilteredElementCollector(self.doc).OfClass(DB.LinePatternElement)
            
            for line_pattern in line_patterns:
                try:
                    pattern_name = line_pattern.Name
                    
                    # Check if this linetype is used in the template
                    # This is a simplified check - in practice, you'd need to check
                    # all category overrides and filter overrides for this pattern
                    linetypes[pattern_name] = {
                        'name': pattern_name,
                        'id': str(line_pattern.Id),
                        'is_used': False  # Placeholder - would need more complex logic to determine actual usage
                    }
                    
                except Exception as e:
                    ERROR_HANDLE.print_note("Error processing line pattern {}: {}".format(pattern_name, str(e)))
                    continue
                    
        except Exception as e:
            ERROR_HANDLE.print_note("Error getting linetype data: {}".format(str(e)))
            
        return linetypes

    def collect_all_template_data(self, template):
        """
        Collect all available data from a template.
        
        Args:
            template: The view template
            
        Returns:
            dict: Complete template data
        """
        try:
            # Get view parameters (returns tuple of controlled and uncontrolled)
            controlled_params, uncontrolled_params = self.get_view_parameters(template)
            
            template_data = {
                'template_name': template.Name,
                'template_id': str(template.Id),
                'category_overrides': self.get_category_overrides(template),
                'category_visibility': self.get_category_visibility(template),
                'workset_visibility': self.get_workset_visibility(template),
                'view_parameters': controlled_params,
                'uncontrolled_parameters': uncontrolled_params,
                'filters': self.get_filter_data(template),
                'import_categories': self.get_import_category_data(template),
                'revit_links': self.get_revit_link_data(template),
                'detail_levels': self.get_detail_level_data(template),
                'linetypes': self.get_linetype_data(template)
            }
            
            return template_data
            
        except Exception as e:
            ERROR_HANDLE.print_note("Error collecting all template data: {}".format(str(e)))
            return None
    


if __name__ == "__main__":
    pass