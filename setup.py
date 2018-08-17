import sys

import setuptools
from openpyn import __data_files__, __version__

if sys.version_info < (3, 5):
    sys.stderr.write("ERROR: openpyn requires Python 3.5 or above." +
                     "Install using 'pip3' instead of just 'pip' \n")
    sys.exit(1)

with open('README.md', encoding='utf-8') as readme_file:
    full_description = readme_file.read()
    readme_file.close()

setuptools.setup(
    name='openpyn',
    version=__version__,
    description='Easily connect to and switch between, OpenVPN servers hosted by NordVPN.',
    license='GNU General Public License v3 or later (GPLv3+)',
    author='JGill',
    zip_safe=False,
    author_email='joty@mygnu.org',
    url='https://github.com/jotyGill/openpyn-nordvpn/',
    keywords=[
        'openvpn wrapper', 'nordvpn', 'nordvpn client', 'secure vpn',
        'vpn wrapper', 'private vpn', 'privacy'],
    install_requires=['requests', 'colorama', 'coloredlogs', 'verboselogs'],
    platforms=['GNU/Linux', 'Ubuntu', 'Debian', 'Kali', 'CentOS', 'Arch', 'Fedora'],
    packages=setuptools.find_packages(),
    entry_points={
        'console_scripts': [
            'openpyn = openpyn.openpyn:main',
            'openpyn-management = openpyn.management.management:main']},
    data_files=__data_files__,
    include_package_data=True,
    exclude_package_data={'openpyn': ['creds', 'credentials', 'install.sh', '.gitignore']},
    long_description=full_description,
    long_description_content_type='text/markdown',
    classifiers=[
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: System Administrators',
        'Topic :: Utilities',
        'Topic :: Security',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)
