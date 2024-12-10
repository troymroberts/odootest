
from odoo import fields, models
import datetime


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def calculate_mondays(self, date_from=False, date_to=False):
        mondays = 0
        while (date_from < date_to):
            if (date_from.weekday() == 0):
                mondays += 1
            date_from += datetime.timedelta(days=1)
        if (mondays == 0):
            mondays = 1
        return mondays
