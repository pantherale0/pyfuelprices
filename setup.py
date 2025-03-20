import re

import setuptools

with open('README.md', 'r', encoding='utf8') as readme_file:
    long_description = readme_file.read()

# Inspiration: https://stackoverflow.com/a/7071358/6064135
with open('pyfuelprices/_version.py', 'r', encoding='utf8') as version_file:
    version_groups = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file.read(), re.M)
    if version_groups:
        version = version_groups.group(1)
    else:
        raise RuntimeError('Unable to find version string!')

REQUIREMENTS = [
    # 'numpy == 1.26.0',
    # 'scikit-learn == 1.3.0',
    'geopy == 2.4.1',
    'voluptuous >= 0.10'
]

DEV_REQUIREMENTS = [
    'bandit >= 1.7,< 1.9',
    'black >= 23,< 26',
    'build >= 0.10,< 1.3',
    'flake8 >= 6,< 8',
    'isort >= 5,< 7',
    'mypy >= 1.5,< 1.16',
    'pytest >= 7,< 9',
    'pytest-cov >= 4,< 7',
    'twine >= 4,< 7',
]

setuptools.setup(
    name='pyfuelprices',
    version=version,
    description='A generic library to collect fuel prices of fuel stations around the world!',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='http://github.com/pantherale0/pyfuelprices',
    author='pantherale0',
    license='MIT',
    packages=setuptools.find_packages(),
    package_data={
        'pyfuelprices': [
            'py.typed',
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=REQUIREMENTS,
    extras_require={
        'dev': DEV_REQUIREMENTS,
    },
    entry_points={
        'console_scripts': [
            'pyfuelprices=pyfuelprices:main',
        ]
    },
    python_requires='>=3.8, <4',
)
