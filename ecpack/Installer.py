
import os
import os.path
import json
import ecpack.sign_executable

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

    def add_file_name(self, file_name, file_size):
        self.file_names.append(file_name)
        self.file_size += file_size

    def executable_file_names(self):
        """Return a list of executables
        """
        return [file_name for file_name in self.file_names if file_name.endswith(".exe")]

    def extract_files(self, zip_file, prefix):
        """Extract all the files of a component.
        The component directory at the root of the zip file is removed from the
        path when stored into the prefix directory.
        Which means with multiple components the files are merged into the same
        directory.

        @param zip_file An open zip file
        @param prefix The directory to store the files in.
        """
        for file_name in self.file_names:
            zip_item = self.name + "/" + file_name
            out_file_name = prefix + "/" + file_name
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
            self.version = package_data["version-string"]
            self.license = package_data["license"]
            self.homepage = package_data["homepage"]
            self.description = package_data["description"]
            self.vendor = package_data["vendor"]

        with zip_file.open("ecpack.json") as ecpack_json:
            ecpack_data = json.load(ecpack_json)
            self.components = Installer.parse_components(ecpack_data, zip_file)

    @classmethod
    def parse_components(cls, ecpack_data, zip_file):
        components = {}
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

                components[component.name] = component

        return components

    def extract_components(self):
        """Extract files from each component and merge them in the same directory
        """
        for component in self.components.values():
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

    def file_exists(self, file_name):
        """Check if a file exists in the zip file
        """
        for zip_info in self.zip_file.infolist():
            if zip_info.filename == file_name:
                return True
        return False

