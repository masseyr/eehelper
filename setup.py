import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="eehelper",
    version="0.0.1",
    author="Richard Massey",
    author_email="rm885@nau.edu",
    description="Helper library for Google Earth Engine python API scripts",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/masseyr/eehelper",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 2",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=2.7.11',
    install_requires=[
        'earthengine-api>=0.1.175',
    ]
)
