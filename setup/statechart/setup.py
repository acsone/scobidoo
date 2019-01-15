import setuptools

setuptools.setup(
    setup_requires=['setuptools-odoo'],
    odoo_addon={
        'external_dependencies_override': {
            'python': {
                'sismic': 'sismic>=1.4.1',
            },
        },
    },
)
