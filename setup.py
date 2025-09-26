#from setuptools import setup, find_packages
from distutils.core import setup

VERSION = '0.0.1' 
DESCRIPTION = 'Qualitative Spatial Representation'
LONG_DESCRIPTION = 'Qualitative Spatial Representation (QSR)'

# Setting up
setup(
       # the name must match the folder name 'verysimplemodule'
        name="DocQSR", 
        version=VERSION,
        author="Mark Bell",
        author_email="mark.bell@nationalarchives.gov.uk",
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        packages=['QSR'],
        requires=['math', 'collections'], # add any additional packages that 
        # needs to be installed along with your package. Eg: 'caer'

        keywords=['python', 'qsr package'],
        classifiers= [
            "Development Status :: 3 - Alpha",
            "Intended Audience :: Cultural Heritage",
            "Programming Language :: Python :: 3",
            "Operating System :: MacOS :: MacOS X",
            "Operating System :: Microsoft :: Windows",
            "Operating System :: Linux :: Linux",
        ]
)
