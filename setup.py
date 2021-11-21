from setuptools import setup
import os
from freecad.xray.compile_resources import compile_resources

version_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 
                            "freecad", "xray", "version.py")
with open(version_path) as fp:
    exec(fp.read())
    
compile_resources()

setup(name='freecad.xray',
      version=str(__version__),
      packages=['freecad',
                'freecad.xray',
                'freecad.xray.xrayCreate',
                'freecad.xray.xrayUtils',
                ],
      maintainer="sanguinariojoe",
      maintainer_email="jlcercos@gmail.com",
      url="https://gitlab.com/sanguinariojoe/freecad.xray",
      description="X-Ray simulator. Created by Jose Luis Cercos Pita",
      install_requires=["numpy", "openexr", "qtrangeslider", "qtrangeslider[pyside2]"],
      include_package_data=True)
