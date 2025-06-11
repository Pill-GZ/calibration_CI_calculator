from setuptools import find_packages, setup

setup(
    name="shiny_app_CI_OTE",
    use_scm_version=False,
    packages=find_packages(".", exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    package_data={"": ["*.pkl"]},
    include_package_data=True,
    url="",
    license="",
    author="data-science",
    author_email="data@upstart.com",
    description="",
    # setup_requires=["setuptools_scm"],
    install_requires=[
        # does not include conda packages, only pip packages
        "numpy>=1.26.0",
        "pandas>=1.5.0",
        "scipy~=1.12.0",
        "statsmodels>=0.14.0",
        "shiny>=0.9.0",
    ],
    python_requires=">=3.11, <4",
)
