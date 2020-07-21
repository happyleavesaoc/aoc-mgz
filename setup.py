"""Setup."""
from setuptools import setup, find_packages

setup(
    name='mgz',
    version='1.4.7',
    description='Parse Age of Empires 2 recorded games.',
    url='https://github.com/happyleavesaoc/aoc-mgz/',
    license='MIT',
    author='happyleaves',
    author_email='happyleaves.tfr@gmail.com',
    packages=find_packages(),
    install_requires=[
        'aiohttp>=3.6.2',
        'construct==2.8.16',
        'flatbuffers>=1.10',
        'tabulate>=0.8.2',
        'tqdm>=4.28.1',
    ],
    entry_points = {
        'console_scripts': ['mgz=mgz.cli:main'],
    },
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
    ]
)
