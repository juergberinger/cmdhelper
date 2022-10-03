from setuptools import setup

def read(fname):
    """Return contents of file with name fname."""
    with open(fname, 'r') as f:
        return f.read()

setup(
    name = 'cmdhelper',
    version = '0.3.0',
    description = 'Python utility for writing command line scripts with consistent look and feel.',
    long_description = read('README.rst'),
    url = 'https://github.com/juergberinger/cmdhelper',
    license = 'MIT',
    author = 'Juerg Beringer',
    author_email = 'juerg.beringer@gmail.com',
    py_modules = ['cmdhelper'],
    include_package_data = True,
    install_requires = ['future'],
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: System :: Shells',
        'Topic :: Utilities'
        ],
    keywords = 'command line utility, scripts',
)
