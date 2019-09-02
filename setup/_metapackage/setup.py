import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo10-addons-acsone-scobidoo",
    description="Meta package for acsone-scobidoo Odoo addons",
    version=version,
    install_requires=[
        'odoo10-addon-statechart',
        'odoo10-addon-statechart_demo_purchase',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
