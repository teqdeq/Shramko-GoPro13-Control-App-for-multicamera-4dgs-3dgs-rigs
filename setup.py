from setuptools import setup, find_packages

setup(
    name="gopro_monitor",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "PyQt5>=5.15.0",
        "requests>=2.25.0",
        "opencv-python>=4.5.0",
        "numpy>=1.19.0",
    ],
    entry_points={
        'console_scripts': [
            'gopro_monitor=status_monitoring.main:main',
        ],
    },
    python_requires='>=3.7',
) 