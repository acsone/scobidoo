import setuptools

setuptools.setup(
    setup_requires=['setuptools-odoo'],
    odoo_addon=True,
    dependency_links=[
        'git+https://github.com/sbidoul/sismic@py27#egg=sismic',
    ],
)
