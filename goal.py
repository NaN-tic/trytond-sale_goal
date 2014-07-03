#The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
from decimal import Decimal
from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import PoolMeta
from trytond.pyson import Eval, If
from trytond.transaction import Transaction

__all__ = ['Distribution', 'DistributionLine', 'Goal', 'GoalDetail']
__metaclass__ = PoolMeta


class Distribution(ModelSQL, ModelView):
    'Goal Distribution'
    __name__ = 'sale.goal.distribution'
    name = fields.Char('Name', required=True)
    lines = fields.One2Many('sale.goal.distribution.detail', 'distribution',
        'Lines')
    total = fields.Function(fields.Numeric('Total', digits=(16, 4)),
        'on_change_with_total')

    @fields.depends('lines')
    def on_change_with_total(self, name=None):
        return sum((x.value for x in self.lines), Decimal('0.0'))


class DistributionLine(ModelSQL, ModelView):
    'Goal Distribution Line'
    __name__ = 'sale.goal.distribution.detail'
    distribution = fields.Many2One('sale.goal.distribution', 'Goal',
        required=True, ondelete='CASCADE')
    name = fields.Char('Name', required=True)
    value = fields.Numeric('Total', digits=(16, 4), required=True)

    @staticmethod
    def default_value():
        return Decimal('0.0')


class Goal(ModelSQL, ModelView):
    'Goal'
    __name__ = 'sale.goal'
    company = fields.Many2One('company.company', 'Company', required=True,
        domain=[
            ('id', If(Eval('context', {}).contains('company'), '=', '!='),
                Eval('context', {}).get('company', -1)),
            ],
        select=True)
    employee = fields.Many2One('company.employee', 'Salesman', required=True,
        domain=[
            ('company', '=', Eval('company', -1)),
            ],
        depends=['company'])
    party = fields.Many2One('party.party', 'Party')
    distribution = fields.Many2One('sale.goal.distribution', 'Distribution')
    account = fields.Many2One('analytic_account.account', 'Account',
            required=True,
        domain=[
            ('type', '!=', 'view'),
            ['OR',
                ('company', '=', None),
                ('company', '=', Eval('company', -1)),
                ],
            ],
        depends=['company'])
    currency_digits = fields.Function(fields.Integer('Currency Digits'),
        'on_change_with_currency_digits')
    amount = fields.Numeric('Amount', required=True,
        digits=(16, Eval('currency_digits', 2)),
        depends=['currency_digits']
        )
    lines = fields.One2Many('sale.goal.detail', 'goal', 'Lines')

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @staticmethod
    def default_employee():
        return Transaction().context.get('employee')

    @fields.depends('company')
    def on_change_with_currency_digits(self, name=None):
        return self.company.currency.digits

    def update_lines(self):
        'Updates lines values based on amount and distribution'
        res = {}
        if self.distribution:
            new_lines = []
            digits = self.currency_digits or 2
            amount = self.amount or Decimal('0.0')
            for index, line in enumerate(self.distribution.lines):
                new_lines.append((index, {
                            'name': line.name,
                            'value': (line.value / self.distribution.total *
                                amount).quantize(Decimal(str(10 ** -
                                        digits))),
                            }))
            if new_lines:
                res['lines'] = {
                    'add': new_lines,
                    'remove': [x.id for x in self.lines],
                    }
        return res

    @fields.depends('lines', 'distribution', 'amount', 'currency_digits')
    def on_change_distribution(self):
        return self.update_lines()

    @fields.depends('lines', 'distribution', 'amount', 'currency_digits')
    def on_change_amount(self):
        return self.update_lines()

    @fields.depends('distribution', 'lines')
    def on_change_lines(self):
        res = {}
        if self.distribution:
            res['distribution'] = None
        return res


class GoalDetail(ModelSQL, ModelView):
    'Goal Detail'
    __name__ = 'sale.goal.detail'
    goal = fields.Many2One('sale.goal', 'Goal', required=True,
        ondelete='CASCADE')
    name = fields.Char('Name', required=True)
    currency_digits = fields.Function(fields.Integer('Currency Digits'),
        'on_change_with_currency_digits')
    value = fields.Numeric('Amount', required=True,
        digits=(16, Eval('currency_digits', 2)),
        depends=['currency_digits']
        )

    @fields.depends('goal')
    def on_change_with_currency_digits(self, name=None):
        return self.goal.currency_digits
