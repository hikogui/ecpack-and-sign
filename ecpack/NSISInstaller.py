
import ecpack.Installer

class NSISInstaller (ecpack.Installer.Installer):
    def __init__(self, zip_file):
        super().__init__(zip_file)

    def make_nsis_uninstaller(self):
        pass

    def make_nsis_installer(self, uninstaller_filename):
        pass

    def create_nsis_installer(self, prefix):
        """Create a nsis installer

        @param prefix Location where the temporary files are stored.
        @return file name of the installer.
        """
        self.extract_components(prefix)

        for component in self.components.values():
            for executable_file_name in component.executable_file_names():
                ecpack.sign_executable.sign_executable(executable_file_name)

        uninstaller_filename = self.make_nsis_uninstaller()
        ecpack.sign_executable.sign_executable(uninstaller_filename)

        installer_filename = self.make_nsis_installer(uninstaller_filename)
        ecpack.sign_executable.sign_executable(installer_filename)

        return installer_filename