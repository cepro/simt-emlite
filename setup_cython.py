import os
from pathlib import Path

from Cython.Build import cythonize
from setuptools import find_packages, setup
from setuptools.extension import Extension


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
        zip_safe=False,
    )


if __name__ == "__main__":
    main()
