import setuptools

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setuptools.setup(
    name='sqlalchemy-faker',
    version='0.0.3',
    author='GongSakura',
    author_email='gongskaura@yahoo.com',
    description='a tool of sqlalchemy for generating fake data',
    long_description=long_description,
    url='https://github.com/GongSakura/SQLAlchemy-Faker',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
)
