from setuptools import setup, find_packages

setup(name='isimgui', version='0.1.3', packages=find_packages(),

 install_requires=[
        "pyqt5",
        "pycromanager",
        "qimage2ndarray",
        "pyqtgraph",
        "pygame",
        "scipy",
        "nidaqmx",
        "wheel",
        "pymm-eventserver"
    ]
)