import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-acsone-scobidoo",
    description="Meta package for acsone-scobidoo Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-statechart>=16.0dev,<16.1dev',
        'odoo-addon-statechart_demo>=16.0dev,<16.1dev',
        'odoo-addon-test_statechart>=16.0dev,<16.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 16.0',
    ]
)
