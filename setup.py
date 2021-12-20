from setuptools import setup, find_packages
import sys

version = '0.0.1'

setup(
    name='demo',
    author='Joe Viveiros',
    author_email='joe.viveiros@verygood.systems',
    version=version,
    description='VGS Demo',
    license='Other/Proprietary License',
    include_package_data=True,
    packages=['.'],
    install_requires=[
        "gunicorn==19.7.1",
        "requests>=2.20.0,<3.0",
        "SQLAlchemy==1.2.12",
        "Flask==1.0.2",
        "Flask-Admin==1.5.5",
        "Flask-SQLAlchemy==2.5.1",
        "Flask-Login==0.4.1",
        "Flask-WTF>=0.14,<0.15",
        "flask-mail>=0.9.1,<0.10.0",
   ],
)
