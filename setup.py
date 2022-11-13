from setuptools import setup, find_packages

setup(
    name='yabu',
    version='2.0.0a',
    py_modules=find_packages(),
    install_requires=[
        'Click',
    ],
    entry_points={
        'console_scripts': [
            'yabu = view.backup_cmd:cli',
        ],
    },
)