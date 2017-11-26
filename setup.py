from setuptools import setup, find_packages

setup(
    name='mgz',
    version='1.1.1',
    description='Parse Age of Empires 2 recorded games.',
    url='https://github.com/happyleavesaoc/aoc-mgz/',
    license='MIT',
    author='happyleaves',
    author_email='happyleaves.tfr@gmail.com',
    packages=find_packages(),
    install_requires=['construct>=2.8.16', 'voobly>=1.0.0'],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
    ]
)
