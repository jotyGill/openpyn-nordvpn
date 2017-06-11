from setuptools import setup, find_packages
from openpyn import __version__
with open('README.rst', encoding='utf-8') as readme_file:
    full_description = readme_file.read()
    readme_file.close()

setup(
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
    install_requires=['requests'],
    platforms=['GNU/Linux', 'Ubuntu', 'Debian', 'Kali', 'CentOS', 'Arch', 'Fedora'],
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'openpyn = openpyn.openpyn:main']},
    package_data={'openpyn': ['README.md', 'LICENSE.md', ]},
    data_files=[('/usr/share/openpyn', ['./openpyn/scripts/manual-dns-patch.sh',
                './openpyn/scripts/update-resolv-conf.sh'])],
    include_package_data=True,
    exclude_package_data={'openpyn': ['creds', 'credentials', 'install.sh', '.gitignore']},
    long_description=full_description,
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
