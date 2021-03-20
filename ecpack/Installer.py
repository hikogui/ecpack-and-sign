
import os
import os.path
import json
import ecpack.sign_executable
import getpass

class Component (object):
    def __init__(self, name, display_name, description, enabled, hidden, required, dependencies):
        self.name = name
        self.display_name = display_name
        self.description = description
        self.enabled = enabled
        self.hidden = hidden
        self.required = required
        self.dependencies = dependencies
        self.file_names = []
        self.file_size = 0

    def directory_names(self):
        """Return a list of directories sorted for adding
        """
        directories = set()
        for file_name in self.file_names:
            dir_name = os.path.dirname(file_name)
            if dir_name != "":
                directories.add(os.path.dirname(file_name))

        return sorted(directories)

    def add_file_name(self, file_name, file_size):
        self.file_names.append(file_name)
        self.file_size += file_size

    def executable_file_names(self):
        """Return a list of executables
        """
        return [file_name for file_name in self.file_names if file_name.endswith(".exe")]

    def extract_files(self, zip_file, prefix):
        """Extract all the files of a component.

        @param zip_file An open zip file
        @param prefix The directory to store the files in.
        """
        for file_name in self.file_names:
            zip_item = self.name + "/" + file_name
            out_file_name = os.path.join(prefix, os.path.normcase(zip_item))
            out_dir_name = os.path.dirname(out_file_name)

            os.makedirs(out_dir_name, exist_ok=True)
            with open(out_file_name, "wb") as out_fd:
                out_fd.write(zip_file.read(zip_item))
                out_fd.close()


class Installer (object):
    def __init__(self, zip_file, prefix):
        self.zip_file = zip_file
        self.prefix = prefix

        with zip_file.open("_cpack/package.json") as package_json:
            package_data = json.load(package_json)
            self.name = package_data["name"]
            self.display_name = package_data["display-name"]
            self.version = package_data["version"]
            self.license = package_data["license"]
            self.homepage = package_data["homepage"]
            self.description = package_data["description"]
            self.vendor = package_data["vendor"]
            self.signtool_fmt = package_data["signtool"]
            self.signtool_password = None

        with zip_file.open("ecpack.json") as ecpack_json:
            ecpack_data = json.load(ecpack_json)
            self.components = Installer.parse_components(ecpack_data, zip_file)

    @classmethod
    def parse_components(cls, ecpack_data, zip_file):
        components = []
        for name, component_data in ecpack_data["components"].items():
            # Ignore all components that start with an underscore.
            if not name.startswith("_"):
                component = Component(
                    name=component_data["name"],
                    display_name=component_data["displayName"],
                    description=component_data["description"],
                    enabled=not component_data["isDisabledByDefault"],
                    hidden=component_data["isHidden"],
                    required=component_data["isRequired"],
                    dependencies=[x for x in component_data["dependencies"] if not x.startswith("_")]
                )

                # Get a list of files belonging to this component.
                component_prefix = name + "/"
                for zip_info in zip_file.infolist():
                    if zip_info.is_dir():
                        continue
                    if not zip_info.filename.startswith(component_prefix):
                        continue
                    component.add_file_name(zip_info.filename[len(component_prefix):], zip_info.file_size)

                components.append(component)

        return components

    def signtool(self, executable_file_name):
        if "{password}" in self.signtool_fmt and self.signtool_password is None:
            self.signtool_password = getpass.getpass("signtool password: ")

        signtool_executable = "c:\\Program Files (x86)\\Windows Kits\\10\\App Certification Kit\\signtool.exe"
        signtool_command = self.signtool_fmt.format(signtool=signtool_executable, executable=executable_file_name, password=self.signtool_password)
        command = '"{}"'.format(signtool_command)

        r = os.system(command)
        if r != 0:
            raise RuntimeError("Failed running signtool: {}".format(command))

    def extract_components(self):
        """Extract files from each component and merge them in the same directory
        """
        for component in self.components:
            component.extract_files(self.zip_file, self.prefix)

    def extract_directory(self, directory):
        for zip_info in self.zip_file.infolist():
            if zip_info.is_dir():
                continue
            if not zip_info.filename.startswith(directory + "/"):
                continue

            out_file_name = self.prefix + "/" + zip_info.filename
            out_dir_name = os.path.dirname(out_file_name)
            os.makedirs(out_dir_name, exist_ok=True)
            with open(out_file_name, "wb") as out_fd:
                out_fd.write(self.zip_file.read(zip_info))
                out_fd.close()

    def redist_file_names(self):
        install_exe_file_names = []
        for zip_info in self.zip_file.infolist():
            if zip_info.is_dir():
                continue
            if zip_info.filename.startswith("_redist/"):
                install_exe_file_names.append(zip_info.filename[8:])

        return sorted(install_exe_file_names)


    def file_exists(self, file_name):
        """Check if a file exists in the zip file
        """
        for zip_info in self.zip_file.infolist():
            if zip_info.filename == file_name:
                return True
        return False

    def file_size(self):
        return sum(x.file_size for x in self.components)

    def major_version(self):
        return int(self.version.split(".")[0])

    def minor_version(self):
        return int(self.version.split(".")[1])
