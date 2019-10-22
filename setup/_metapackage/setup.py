import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo13-addons-acsone-scobidoo",
    description="Meta package for acsone-scobidoo Odoo addons",
    version=version,
    install_requires=[
        'odoo13-addon-statechart',
        'odoo13-addon-test_statechart',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
