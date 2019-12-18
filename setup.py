import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
        name='sacp',
        version='0.5',
        install_requires=[
            'pygments'
        ],
        author='catatonicprime',
        author_email='catatonicprime@gmail.com',
        description='A simple Apache Config Parser',
        long_description=long_description,
        long_description_content_type='text/markdown',
        url='https://github.com/catatonicprime/sacp',
        packages=setuptools.find_packages(),
        classifiers=[
            'Programming Language :: Python :: 3',
            'License :: OSI Approved :: MIT License',
            'Operating System :: OS Independent',
            ],
        )
