from setuptools import find_packages, setup


setup(
    name="depreciate-for-ledger",
    version="1.0.0",
    description="Generate Ledger transactions for asset depreciation",
    py_modules=["Depreciation", "depreciate"],
    packages=find_packages(),
    entry_points={"console_scripts": ["depreciate=depreciate:main"]},
)