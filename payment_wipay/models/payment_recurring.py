# payment_wipay/models/payment_recurring.py

from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class PaymentRecurring(models.Model):
    _name = 'payment.recurring.wipay'
    _description = 'WiPay Recurring Payment'

    name = fields.Char('Description', required=True)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    token_id = fields.Many2one('payment.token', string='Payment Token', required=True)
    amount = fields.Monetary('Amount', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True)
    interval = fields.Selection([
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly')
    ], string='Interval', required=True)
    next_payment = fields.Date('Next Payment Date', required=True)
    state = fields.Selection([
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='active', required=True)
    payment_count = fields.Integer('Payment Count', default=0)
    last_payment = fields.Date('Last Payment Date')
    
    @api.model
    def _cron_process_recurring_payments(self):
        """Cron job to process due recurring payments."""
        due_payments = self.search([
            ('state', '=', 'active'),
            ('next_payment', '<=', fields.Date.today())
        ])
        
        for payment in due_payments:
            try:
                payment._process_recurring_payment()
            except Exception as e:
                # Log error but continue with other payments
                _logger.exception(
                    "Error processing recurring payment %s: %s",
                    payment.id, str(e)
                )

    def _process_recurring_payment(self):
        """Process a single recurring payment."""
        self.ensure_one()
        
        # Create transaction
        tx_values = {
            'amount': self.amount,
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.id,
            'token_id': self.token_id.id,
            'provider_id': self.token_id.provider_id.id,
            'operation': 'offline',
            'is_recurring': True,
        }
        
        tx = self.env['payment.transaction'].sudo().create(tx_values)
        
        try:
            # Process payment using stored token
            tx._send_payment_request()
            
            if tx.state == 'done':
                # Update recurring payment record
                self.write({
                    'last_payment': fields.Date.today(),
                    'payment_count': self.payment_count + 1,
                    'next_payment': self._compute_next_payment_date()
                })
            else:
                raise ValidationError(_(
                    "Recurring payment failed: %s", tx.state_message
                ))
                
        except Exception as e:
            # Handle failure
            self.message_post(
                body=_("Failed to process recurring payment: %s", str(e))
            )
            raise

    def _compute_next_payment_date(self):
        """Compute the next payment date based on interval."""
        self.ensure_one()
        today = fields.Date.today()
        
        if self.interval == 'weekly':
            return today + relativedelta(weeks=1)
        elif self.interval == 'monthly':
            return today + relativedelta(months=1)
        else:  # yearly
            return today + relativedelta(years=1)

    def action_pause(self):
        """Pause recurring payments."""
        self.write({'state': 'paused'})

    def action_resume(self):
        """Resume recurring payments."""
        self.write({
            'state': 'active',
            'next_payment': fields.Date.today()
        })

    def action_cancel(self):
        """Cancel recurring payments."""
        self.write({'state': 'cancelled'})