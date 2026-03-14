import os
import glob


def resolve_folder(folder_name):
    """
    Converts common folder names into real system paths.
    """
    home = os.path.expanduser("~")

    folders = {
        "desktop": os.path.join(home, "Desktop"),
        "downloads": os.path.join(home, "Downloads"),
        "documents": os.path.join(home, "Documents"),
        "pictures": os.path.join(home, "Pictures")
    }

    folder_name = folder_name.lower()

    if folder_name in folders:
        return folders[folder_name]
    else:
        return os.path.abspath(os.path.expanduser(folder_name))


def list_files(folder):
    folder = resolve_folder(folder)

    files = os.listdir(folder)
    file_paths = []

    for file in files:
        full_path = os.path.join(folder, file)
        if os.path.isfile(full_path):
            file_paths.append(full_path)

    return file_paths


def find_files_by_type(folder, extension):
    folder = resolve_folder(folder)
    pattern = os.path.join(folder, f"*{extension}")
    return glob.glob(pattern)


def scan_folder_recursive(folder):
    folder = resolve_folder(folder)

    all_files = []

    for root, dirs, files in os.walk(folder):
        for file in files:
            full_path = os.path.join(root, file)
            all_files.append(full_path)

    return all_files


