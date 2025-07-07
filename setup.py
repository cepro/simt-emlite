import os
import shutil
from pathlib import Path

from Cython.Build import cythonize
from setuptools import find_packages, setup
from setuptools.command.build_py import build_py
from setuptools.extension import Extension


class CustomBuildPy(build_py):
    """Custom build_py that excludes .py files when .so extensions exist"""

    def find_package_modules(self, package, package_dir):
        modules = super().find_package_modules(package, package_dir)

        # Get list of extension modules
        extensions = getattr(self.distribution, "ext_modules", [])
        extension_names = {ext.name for ext in extensions}

        # Filter out .py files that have corresponding .so extensions
        filtered_modules = []
        for pkg, module, module_file in modules:
            module_name = f"{pkg}.{module}" if pkg else module
            if module_name not in extension_names:
                filtered_modules.append((pkg, module, module_file))

        return filtered_modules


def get_extensions(package_name):
    """Find all .py files and create Extension objects"""
    extensions = []
    package_path = Path(package_name)

    for py_file in package_path.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue  # Skip __init__.py files

        # Convert file path to module name
        relative_path = py_file.relative_to(package_path.parent)
        module_name = str(relative_path.with_suffix("")).replace(os.sep, ".")

        extensions.append(
            Extension(
                module_name,
                [str(py_file)],
                language="c++",
            )
        )

    return extensions


class CythonBuildCommand:
    def __init__(self, package_name):
        self.package_name = package_name

    def run(self):
        # Build extensions
        extensions = get_extensions(self.package_name)

        # Create a temporary directory structure with only the files we want
        temp_package = Path("temp_build") / self.package_name
        temp_package.mkdir(parents=True, exist_ok=True)

        # Copy only __init__.py files to maintain package structure
        for init_file in Path(self.package_name).rglob("__init__.py"):
            relative_path = init_file.relative_to(self.package_name)
            dest = temp_package / relative_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(init_file, dest)

        # Setup with Cython extensions
        setup(
            name="simt-emlite",
            version="0.21.4",
            ext_modules=cythonize(
                extensions,
                compiler_directives={
                    "language_level": "3",
                    "boundscheck": False,
                    "wraparound": False,
                    "nonecheck": False,
                },
                build_dir="build",
            ),
            packages=find_packages(exclude=["tests", "tests.*", "temp_build"]),
            cmdclass={"build_py": CustomBuildPy},
            zip_safe=False,
        )


def main():
    package_name = "simt_emlite"
    builder = CythonBuildCommand(package_name)
    builder.run()


if __name__ == "__main__":
    main()
