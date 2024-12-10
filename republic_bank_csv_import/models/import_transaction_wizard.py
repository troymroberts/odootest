from odoo import models, fields, api
import base64
import csv
from io import StringIO
from odoo.exceptions import UserError
from datetime import datetime



class ImportTransactionWizard(models.TransientModel):
    _name = 'import.transaction.wizard'
    _description = 'Import Transactions Wizard'

    file = fields.Binary('File')
    filename = fields.Char('Filename')

    def import_transactions(self):
        if not self.file:
            raise UserError('Please upload a file.')

        decoded_file = base64.b64decode(self.file)
        file_content = StringIO(decoded_file.decode('utf-8'))
        reader = csv.reader(file_content)
        
        bank_account_no = None
        transactions = []

        for i, row in enumerate(reader):
            if i == 2:  # Bank account number is in the third row
                account_info = row[2]
                possible_dashes = ['–', '-', '—']
                for dash in possible_dashes:
                    if dash in account_info:
                        bank_account_no = account_info.split(dash)[-1].strip()
                        break
                print(f"Extracted bank account number: {bank_account_no}")  # Debug print
            elif i > 12 and row:  # Transactions start from the fourth row onwards
                try:
                    transaction_date = datetime.strptime(row[3], '%d-%m-%Y %H:%M:%S')
                except ValueError:
                    raise UserError(f"Invalid date format in row {i + 1}: {row[1]}")
                transaction = {
                    'date': transaction_date,
                    'description': row[5],
                    'amount': float(row[8]),
                    'type': row[6],
                    'currency': row[7],
                    'cheque': row[9],
                }
                transactions.append(transaction)
        
        if not bank_account_no:
            raise UserError('Bank account number not found.')
        bank_account = self.env['res.partner.bank'].search([('acc_number', '=', bank_account_no)], limit=1)
        if not bank_account:
            raise UserError('Bank account not found.')

        # Ensure the journal has a suspense account
        journal = bank_account.journal_id
        if not journal.suspense_account_id:
            raise UserError('The journal associated with this bank account does not have a suspense account set.')


        currency_id = self.env.company.currency_id
        statement_name = 'Imported Bank Statement'
        statement_name = '{} - {}'.format(statement_name, fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        statement = self.env['account.bank.statement'].create({
            'name': statement_name,
            'date': fields.Date.today(),
            'journal_id': bank_account.journal_id.id,
        })

        for transaction in transactions:
            transaction_currency = self.env['res.currency'].search([('name', '=', transaction['currency'])], limit=1)
            statement_line_values = {
                'date': transaction['date'],
                'payment_ref': transaction['description'],
                'payment_reference':transaction['description'],
                'amount': transaction['amount'],
                'statement_id': statement.id,
                'journal_id': bank_account.journal_id.id
            }

            if transaction_currency and transaction_currency != currency_id:
                statement_line_values['foreign_currency_id'] = transaction_currency.id
                statement_line_values['amount_currency'] = transaction['amount']

            if transaction['cheque']:
                statement_line_values['payment_ref'] = transaction['cheque']

            self.env['account.bank.statement.line'].create(statement_line_values)


        # return {
        #     'type': 'ir.actions.act_window',
        #     'res_model': 'account.bank.statement',
        #     'view_mode': 'form',
        #     'res_id': statement.id,
        #     'target': 'current',
        # }
        return journal.action_open_reconcile()

