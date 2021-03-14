#!/usr/bin/env python3

import sys
import argparse
import zipfile
import json
import ecpack.NSISInstaller

def parse_options(argv):
    parser = argparse.ArgumentParser(description="Prepare NSIS installer")
    parser.add_argument(
        "input_zip",
        type=str,
        help="The ecpack zip containing the contents of the package")

    parser.add_argument(
        "--build-dir",
        action="store",
        default=".",
        help="Directory where to extract the ecpack zip file and create the installer"
    )

    return parser.parse_args(argv)

def main():
    options = parse_options(sys.argv[1:])
    input_zip = options.input_zip
    prefix = options.build_dir

    with zipfile.ZipFile(input_zip, "r") as zip_file:
        installer = ecpack.NSISInstaller.NSISInstaller(zip_file, prefix)
        file_name = installer.create_installer()
        print("Installer '{}' created successfully.".format(file_name))

if __name__ == "__main__":
    main()