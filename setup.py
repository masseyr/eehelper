import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="eehelper",
    version="0.1.3",
    author="Richard Massey",
    author_email="rm885@nau.edu",
    description="Helper library for Google Earth Engine python API scripts",
    license='MIT License',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/masseyr/eehelper",
    packages=setuptools.find_packages(),
    classifiers=[
        'Topic :: Scientific/Engineering :: GIS',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Operating System :: OS Independent',
    ],
    install_requires=[
        'earthengine-api>=0.1.175',
    ],
    keywords='geospatial earthengine spatial google earth science satellite landsat modis',
)
