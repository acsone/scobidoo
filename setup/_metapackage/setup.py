import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo11-addons-acsone-scobidoo",
    description="Meta package for acsone-scobidoo Odoo addons",
    version=version,
    install_requires=[
        'odoo11-addon-statechart',
        'odoo11-addon-test_statechart',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 11.0',
    ]
)
