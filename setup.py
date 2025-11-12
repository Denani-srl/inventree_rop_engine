"""
Setup script for InvenTree ROP Suggestion Engine Plugin
"""

from setuptools import setup, find_packages

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='inventree-rop-suggestion',
    version='1.0.0',
    description='Prescriptive Reorder Point calculation and procurement suggestion engine for InvenTree',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Custom Development',
    author_email='',
    url='https://github.com/yourusername/inventree-rop-suggestion',
    license='MIT',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    
    python_requires='>=3.9',
    
    install_requires=[
        'django>=3.2',
        'djangorestframework>=3.12',
        'inventree>=0.13.0',
    ],
    
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Manufacturing',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Framework :: Django',
        'Topic :: Office/Business',
    ],
    
    keywords='inventree inventory reorder-point rop procurement supply-chain',
    
    entry_points={
        'inventree_plugins': [
            'ROPSuggestionPlugin = inventree_rop_engine:ROPSuggestionPlugin'
        ]
    },
)
