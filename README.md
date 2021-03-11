ecpack-and-sign
===============
External CPack packer and code signing.

External CPack format
---------------------
The external CPack format is a .zip file with the following items in the root of that .zip file:

 - `package_name`.json
 - `component`/
 - \_cpack/NSIS/
 - \_redist/

### `package_name`.json
There is a json file in the root of the .zip file, which describes the components and
their dependencies.

The format of this json file is described in the [CPack External Generator] documentation.

Any component which starts with an underscore will not be part of the generated installer or
uninstaller.

[CPack External Generator]: https://cmake.org/cmake/help/latest/cpack_gen/external.html

### `component`/
These are the files of a component, to be installed on the user's computer.
Individual components may be selected by the user.

Multiple components will be installed in the same install directory.

### \_redist/
Any executable in this directory is added to the installer. During installation
on the user's machine each of those executable is called sequentually in alphabetical order.

After all executables have been executed they are removed from the user's machine.

### \_cpack/NSIS/
This directory contains files used with the NSIS package manager.
