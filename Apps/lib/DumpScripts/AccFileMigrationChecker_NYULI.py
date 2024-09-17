import os
import asyncio
import winsound
import time
from tqdm import tqdm
from colorama import Fore, Style
from datetime import datetime, timedelta
import shutil

class ACCMigrationChecker:
    def __init__(self, project_folder, folder_names_to_check, acc_project_name, acc_project_inner_folder_name, prefix, limit):
        """
        Initialize the ACCMigrationChecker class with project details and path length limit.

        Args:
            project_folder (str): Path to the project folder.
            folder_names_to_check (list): List of folder names to check for exclusion.
            acc_project_name (str): Name of the ACC project.
            acc_project_inner_folder_name (str): Folder name in the ACC project.
            prefix (str): Prefix path for ACC migration.
            limit (int): Maximum allowed path length.
        """
        self.project_folder = project_folder
        self.acc_project_name = acc_project_name
        self.folder_names_to_check = folder_names_to_check
        self.acc_project_inner_folder_name = acc_project_inner_folder_name
        self.prefix = prefix
        self.limit = limit

        self.job_number = os.path.basename(project_folder)
        self.report_folder = f"L:\\4b_Applied Computing\\EnneadTab-DB\\ACC Migrate Path Length Report\\_Projects Specific Report"

    async def check_path_length(self, job_folder):
        """
        Check if any file path will exceed the defined length limit after adding the prefix.

        Args:
            job_folder (str): The job folder to check.

        Returns:
            list: A list of tuples containing the original and new paths for files that exceed the limit.
        """
        affected_files = []
        file_paths = []

        # Collect all file paths first
        for root, _, files in os.walk(job_folder):
            for file in files:
                full_path = os.path.join(root, file)
                full_path_folders = os.path.normpath(root).split(os.sep)

                # If any folder in folder_names_to_check is found in the full path folders, PROCESS
                if any(folder in full_path_folders for folder in self.folder_names_to_check):
                    file_paths.append(full_path)

        # Progress bar using tqdm
        with tqdm(total=len(file_paths), desc=Fore.GREEN + f"Checking files in {os.path.basename(job_folder)}" + Style.RESET_ALL, 
                  unit="file", bar_format="{l_bar}{bar:20}{r_bar}{bar:-10b}") as pbar:
            for original_path in file_paths:
                new_path = self.prefix + "\\" + self.acc_project_name + "\\" + "Project Files" + "\\" + self.acc_project_inner_folder_name + "\\" + original_path.replace(job_folder, "")
                new_path = new_path.replace("\\\\", "\\")

                if len(new_path) > self.limit:
                    file_info = os.stat(original_path)
                    creation_time = datetime.fromtimestamp(file_info.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
                    modified_time = datetime.fromtimestamp(file_info.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    accessed_time = datetime.fromtimestamp(file_info.st_atime).strftime('%Y-%m-%d %H:%M:%S')

                    affected_files.append((original_path, new_path, creation_time, modified_time, accessed_time))

                pbar.update(1)

        return affected_files

    def generate_report_content(self, job_folder, affected_files, elapsed_time):
        """
        Generate the content for the report based on affected files.

        Args:
            job_folder (str): The job folder being checked.
            affected_files (list): List of files that exceed the length limit.
            elapsed_time (float): Time taken to perform the check.

        Returns:
            str: Report content as a string.
        """
        report_content = []

        # Add timestamp at the header
        report_generated_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        report_content.append(f"Report generated on: {report_generated_time}\n")
        report_content.append("="*80 + "\n")

        current_time = datetime.now()
        one_month_ago = current_time - timedelta(days=30)

        recent_files = []
        older_files = []

        for original, new, creation_time, modified_time, accessed_time in affected_files:
            accessed_datetime = datetime.strptime(accessed_time, '%Y-%m-%d %H:%M:%S')
            modified_datetime = datetime.strptime(modified_time, '%Y-%m-%d %H:%M:%S')
            creation_datetime = datetime.strptime(creation_time, '%Y-%m-%d %H:%M:%S')

            # Files accessed, modified, or created in the last 30 days
            if accessed_datetime > one_month_ago or modified_datetime > one_month_ago or creation_datetime > one_month_ago:
                recent_files.append((original, new, creation_time, modified_time, accessed_time))
            else:
                older_files.append((original, new, creation_time, modified_time, accessed_time))

        if recent_files:
            report_content.append(f"Summary: {len(recent_files)} files were accessed, modified, or created in the last 30 days and will be affected.\n")
            report_content.append(f"Note: The warning limit is set to {self.limit} characters. The real limit is 256.\n")
            report_content.append("\n\n" + "="*80 + "\n\n")
            report_content.append("Details of recent files:\n")
            for i, (original, new, creation_time, modified_time, accessed_time) in enumerate(recent_files):
                report_content.append(f"{i+1}. Original: {original}\nNew: {new}\nLength: {len(original)} -> {len(new)}\n"
                                      f"Created: {creation_time}\nModified: {modified_time}\nAccessed: {accessed_time}\n")

        report_content.append("\n\n" + "="*80 + "\n\n")

        if older_files:
            report_content.append(f"Summary: {len(older_files)} files were accessed, modified, or created more than 30 days ago and will be affected.\n")
            for i, (original, new, creation_time, modified_time, accessed_time) in enumerate(older_files):
                report_content.append(f"{i+1}. Original: {original}\nNew: {new}\nLength: {len(original)} -> {len(new)}\n"
                                      f"Created: {creation_time}\nModified: {modified_time}\nAccessed: {accessed_time}\n")

        if not affected_files:
            report_content.append(f"Summary: All paths are below {self.limit} length limit.\n")

        report_content.append(f"\nTotal time taken: {elapsed_time:.2f} seconds\n")
        return "\n".join(report_content)

    def save_text_report(self, project_folder, report_content, status):
        """
        Save the generated report to a file and open it automatically.

        Args:
            project_folder (str): The project folder name.
            report_content (str): The report content to save.
            status (str): The status indicating whether the project is "good" or "bad".
        """
        txt_filename = f"Acc Migration Filepath Length PreCheck [{self.job_number}]_{status}.txt"
        txt_output_path = os.path.join(self.report_folder, txt_filename)

        # Attempt to create the report folder if it doesn't exist
        if not os.path.exists(self.report_folder):
            try:
                os.makedirs(self.report_folder)
            except PermissionError:
                # If we can't create the report folder due to permission error,
                # we will set the report_folder to the desktop folder
                self.report_folder = os.path.join(os.path.expanduser("~"), "Desktop")
                txt_output_path = os.path.join(self.report_folder, txt_filename)

        # Attempt to remove existing reports with the same job number
        try:
            for file in os.listdir(self.report_folder):
                if file.startswith(f"Acc Migration Filepath Length PreCheck [{self.job_number}]_"):
                    os.remove(os.path.join(self.report_folder, file))
        except PermissionError:
            # If we cannot remove files due to permission error, ignore and proceed
            pass

        try:
            # Try to write the report to the intended report folder
            with open(txt_output_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            os.startfile(txt_output_path)
        except (UnicodeEncodeError, PermissionError) as e:
            # If we can't write to the report folder, write to the desktop instead
            desktop_folder = os.path.join(os.path.expanduser("~"), "Desktop")
            error_txt_filename = f"Acc Migration Filepath Length PreCheck [{self.job_number}]_{status}_error.txt"
            error_txt_output_path = os.path.join(desktop_folder, error_txt_filename)
            try:
                with open(error_txt_output_path, 'w', encoding='utf-8', errors='ignore') as f:
                    f.write(report_content)
                os.startfile(error_txt_output_path)
            except Exception as e:
                # If we cannot write to desktop either, print an error message
                print(f"Failed to write report to desktop: {e}")
        finally:
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)

    async def copy_files_to_acc(self, project_folder, folder_names_to_check, acc_project_name, acc_project_inner_folder_name, real_acc_prefix):
        """
        Asynchronously copy the project folder to the ACC project.

        Args:
            project_folder (str): Path to the project folder.
            folder_names_to_check (list): List of folders to check.
            acc_project_name (str): Name of the ACC project.
            acc_project_inner_folder_name (str): Folder name in the ACC project.
            real_acc_prefix (str): Prefix path for ACC migration.
        """

        out = []
        total_size = 0  # Initialize total size to zero
        is_real_copy = False

        for folder in folder_names_to_check:
            working_folder = os.path.join(project_folder, folder)
            for root, dirs, files in os.walk(working_folder):
                for file in files:
                    original_path = os.path.join(root, file)
                    relative_path = os.path.relpath(original_path, project_folder)
                    target_path = os.path.join(real_acc_prefix, acc_project_name, "Project Files", acc_project_inner_folder_name, relative_path)

                    # Add the prefix "&#&_" to the filename
                    if is_real_copy:
                        target_folder, filename = os.path.split(target_path)
                        target_path = os.path.join(target_folder, "&#&_" + filename)

                    out.append(target_path)

                    # Calculate the size of the original file and add it to the total size
                    file_size = os.path.getsize(original_path)
                    total_size += file_size

                    if is_real_copy:
                        # Simulate async I/O-bound operation for copying files
                        await asyncio.sleep(0)

                        if not os.path.exists(target_folder):
                            os.makedirs(target_folder)

                        shutil.copy2(original_path, target_path)

        # Function to format the size into human-readable form
        def format_size(size_in_bytes):
            # 1 KB = 1024 bytes
            for unit in ['bytes', 'KB', 'MB', 'GB', 'TB']:
                if size_in_bytes < 1024 or unit == 'TB':
                    return f"{size_in_bytes:.2f} {unit}"
                size_in_bytes /= 1024

        copy_note = "REAL_COPY" if is_real_copy else "SIMULATED_COPY"
        txt_filename = f"Acc Migration Filepath Length PreCheck [{self.job_number}]_{copy_note}.txt"
        log_file = os.path.join(self.report_folder, txt_filename)

        # Get current time for the timestamp
        report_generated_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Try to write the log file to the intended report folder
        try:
            with open(log_file, "w", encoding="utf-8") as f:
                # Write the timestamp at the header
                f.write(f"Report generated on: {report_generated_time}\n")
                f.write("=" * 80 + "\n")
                total_size_formatted = format_size(total_size)
                f.write(f"Total size: {total_size_formatted}\n")
                f.write(f"Total files: {len(out)}\n")
                f.write("=" * 80 + "\n")
                f.writelines(f"{idx:04d}. {path}\n" for idx, path in enumerate(out, start=1))
            os.startfile(log_file)
        except PermissionError:
            # If we can't write to the report folder, write to the desktop instead
            desktop_folder = os.path.join(os.path.expanduser("~"), "Desktop")
            log_file = os.path.join(desktop_folder, txt_filename)
            try:
                with open(log_file, "w", encoding="utf-8") as f:
                    # Write the timestamp at the header
                    f.write(f"Report generated on: {report_generated_time}\n")
                    f.write("=" * 80 + "\n")
                    total_size_formatted = format_size(total_size)
                    f.write(f"Total size: {total_size_formatted}\n")
                    f.write(f"Total files: {len(out)}\n")
                    f.write("=" * 80 + "\n")
                    f.writelines(f"{idx:04d}. {path}\n" for idx, path in enumerate(out, start=1))
                os.startfile(log_file)
            except Exception as e:
                # If we cannot write to desktop either, print an error message
                print(f"Failed to write log file to desktop: {e}")

async def process_project_check(project_folder, folder_names_to_check, acc_project_name, acc_project_inner_folder_name, prefix, limit):
    """
    Process the project folder and generate the report.

    Args:
        project_folder (str): Path to the project folder.
        folder_names_to_check (list): List of folders to check.
        acc_project_name (str): Name of the ACC project.
        acc_project_inner_folder_name (str): Folder name in the ACC project.
        prefix (str): Prefix path for ACC migration.
        limit (int): Maximum allowed path length.
    """
    checker = ACCMigrationChecker(project_folder, folder_names_to_check, acc_project_name, acc_project_inner_folder_name, prefix, limit)

    # Perform the path length check
    start_time = time.time()
    affected_files = await checker.check_path_length(project_folder)
    elapsed_time = time.time() - start_time

    report_content = checker.generate_report_content(project_folder, affected_files, elapsed_time)
    status = "bad" if affected_files else "good"
    checker.save_text_report(project_folder, report_content, status)

    print(f"\nTotal time taken for {project_folder}: {elapsed_time:.2f} seconds\n")
    print("="*80)

    return affected_files

async def process_project_copy(project_folder, folder_names_to_check, acc_project_name, acc_project_inner_folder_name, real_acc_prefix):
    """
    Process the project folder and copy files to ACC asynchronously.

    Args:
        project_folder (str): Path to the project folder.
        folder_names_to_check (list): List of folders to check.
        acc_project_name (str): Name of the ACC project.
        acc_project_inner_folder_name (str): Folder name in the ACC project.
        real_acc_prefix (str): Path to the ACC project.
    """
    checker = ACCMigrationChecker(project_folder, folder_names_to_check, acc_project_name, acc_project_inner_folder_name, "", 0)

    # Copy files asynchronously to ACC
    await checker.copy_files_to_acc(project_folder, folder_names_to_check, acc_project_name, acc_project_inner_folder_name, real_acc_prefix)


def main():
    prefix_template = "C:\\Users\\{}\\DC\\ACCDocs\\Ennead Architects LLP"
    limit = 245

    my_project = "J:\\2151"
    acc_project_name = "2151_NYULI"
    acc_project_inner_folder_name = "00_2151"
    folder_names_to_check = [
        "2_Record",
        "1_Presentation\\01_P-Image",
        "2_Master File",
        "0_Progress Set"
    ]

    real_acc_prefix = prefix_template.format(os.getlogin())
    # Run the file copy task
    asyncio.run(process_project_copy(my_project, folder_names_to_check, acc_project_name, acc_project_inner_folder_name, real_acc_prefix))

    generic_acc_account_prefix = prefix_template.format("USER.NAME")
    # Run the path length check task
    asyncio.run(process_project_check(my_project, folder_names_to_check, acc_project_name, acc_project_inner_folder_name, generic_acc_account_prefix, limit))



if __name__ == "__main__":
    main()
