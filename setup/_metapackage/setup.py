import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo9-addons-acsone-scobidoo",
    description="Meta package for acsone-scobidoo Odoo addons",
    version=version,
    install_requires=[
        'odoo9-addon-statechart',
        'odoo9-addon-statechart_demo_purchase',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
