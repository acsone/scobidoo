import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo13-addons-odoo12-addons-acsone-scobidoo",
    description="Meta package for odoo12-addons-acsone-scobidoo Odoo addons",
    version=version,
    install_requires=[
        'odoo13-addon-statechart',
        'odoo13-addon-statechart_demo_purchase',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
