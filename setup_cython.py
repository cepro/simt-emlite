import os
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


def main():
    package_name = "simt_emlite"  # Fixed: use underscore not hyphen

    extensions = get_extensions(package_name)

    setup(
        name=package_name,
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
        packages=find_packages(),
        cmdclass={"build_py": CustomBuildPy},
        zip_safe=False,
    )


if __name__ == "__main__":
    main()
