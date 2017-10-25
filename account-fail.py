import odoorpc

# 10.0
odoo = odoorpc.ODOO('190978-10-0-854ab6.runbot10.odoo.com', port=80)
odoo.login('190978-10-0-854ab6-all', 'admin', 'admin')

# 9.0
# odoo = odoorpc.ODOO('190965-9-0-d99573.runbot5.odoo.com', port=80)
# odoo.login('190965-9-0-d99573-all', 'admin', 'admin')

AccountAccount = odoo.env['account.account']
AccountJournal = odoo.env['account.journal']
AccountMove = odoo.env['account.move']

aj = AccountJournal.search([('code', '=', 'MISC')])
assert aj

aa = AccountAccount.search([('code', '=like', '10%')])
assert len(aa) > 1

am = AccountMove.create({
    'name': '/',
    'journal_id': aj[0],
    'line_ids': [
        (0, 0, {
            'name': '...',
            'account_id': aa[0],
            'debit': 100,
            'credit': 0,
        }),
        (0, 0, {
            'name': '...',
            'account_id': aa[1],
            'debit': 0,
            'credit': 100,
        }),
    ],
})
AccountMove.post([am])
# it should not be possible to change the date of a posted entry
AccountMove.write([am], {'date': '2016-01-01'})
