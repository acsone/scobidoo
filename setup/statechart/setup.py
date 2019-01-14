import setuptools

setuptools.setup(
    setup_requires=['setuptools-odoo'],
    odoo_addon={
        'external_dependencies_override': {
            'python': {
                # https://github.com/AlexandreDecan/sismic/issues/89
                'sismic': 'sismic==1.3',
            },
        },
    },
)
