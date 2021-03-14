
import subprocess
import os.path
import os
import ecpack.Installer
import ecpack.psp

class NSISInstaller (ecpack.Installer.Installer):
    def __init__(self, zip_file, prefix):
        super().__init__(zip_file, prefix)

    def makensis_exe_filename(self):
        return "c:\\Program Files (x86)\\NSIS\\makensis.exe"

    def installer_nsi_in_filename(self):
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "installer.nsi.in"))

    def installer_nsi_filename(self):
        return os.path.abspath(os.path.join(self.prefix, "installer.nsi"))

    def uninstall_exe_filename(self):
        return os.path.abspath(os.path.join(self.prefix, "uninstall.exe"))

    def install_exe_filename(self):
        filename = "install-" + self.name + "-v" + self.version.replace(".", "-") + ".exe"
        return os.path.abspath(os.path.join(self.prefix, filename))

    def create_uninstaller_exe_filename(self):
        return os.path.abspath(os.path.join(self.prefix, "create_uninstaller.exe"))

    def create_installer_nsi(self):
        template_text = open(self.installer_nsi_in_filename(), "r").read()
        text = ecpack.psp.psp(template_text, {"self": self})
        with open(self.installer_nsi_filename(), "w") as out_fd:
            out_fd.write(text)

    def create_uninstaller(self):
        # We must use os.system to cause UAC to elevate the privilages of the create_uninstaller.exe
        os.system('""{}" /DCREATE_UNINSTALLER "{}""'.format(self.makensis_exe_filename(), self.installer_nsi_filename()))

        os.system('""{}" /S"'.format(self.create_uninstaller_exe_filename()))


    def create_installer(self):
        """Create a nsis installer

        @return file name of the installer.
        """
        self.extract_components()
        self.extract_directory("_redist")
        self.extract_directory("_cpack")

        for component in self.components.values():
            for executable_file_name in component.executable_file_names():
                ecpack.sign_executable.sign_executable(executable_file_name)

        self.create_installer_nsi()
        self.create_uninstaller()
        ecpack.sign_executable.sign_executable(self.uninstall_exe_filename())

        os.system('""{}" "{}""'.format(self.makensis_exe_filename(), self.installer_nsi_filename()))
        ecpack.sign_executable.sign_executable(self.install_exe_filename())

        return self.install_exe_filename()
