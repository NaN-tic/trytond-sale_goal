==================
Sale Goal Scenario
==================

=============
General Setup
=============

Imports::

    >>> import datetime
    >>> from dateutil.relativedelta import relativedelta
    >>> from decimal import Decimal
    >>> from proteus import config, Model, Wizard
    >>> today = datetime.date.today()

Create database::

    >>> config = config.set_trytond()
    >>> config.pool.test = True

Install account_asset::

    >>> Module = Model.get('ir.module.module')
    >>> modules = Module.find([
    ...     ('name', '=', 'sale_goal'),
    ... ])
    >>> Module.install([x.id for x in modules], config.context)
    >>> Wizard('ir.module.module.install_upgrade').execute('upgrade')

Create company::

    >>> Currency = Model.get('currency.currency')
    >>> CurrencyRate = Model.get('currency.currency.rate')
    >>> Company = Model.get('company.company')
    >>> Party = Model.get('party.party')
    >>> company_config = Wizard('company.company.config')
    >>> company_config.execute('company')
    >>> company = company_config.form
    >>> party = Party(name='Dunder Mifflin')
    >>> party.save()
    >>> company.party = party
    >>> currencies = Currency.find([('code', '=', 'USD')])
    >>> if not currencies:
    ...     currency = Currency(name='US Dollar', symbol=u'$', code='USD',
    ...         rounding=Decimal('0.01'), mon_grouping='[]',
    ...         mon_decimal_point='.', mon_thousands_sep=',')
    ...     currency.save()
    ...     CurrencyRate(date=today + relativedelta(month=1, day=1),
    ...         rate=Decimal('1.0'), currency=currency).save()
    ... else:
    ...     currency, = currencies
    >>> company.currency = currency
    >>> company_config.execute('add')
    >>> company, = Company.find()

Reload the context::

    >>> User = Model.get('res.user')
    >>> config._context = User.get_preferences(True, config.context)

Create fiscal year::

    >>> FiscalYear = Model.get('account.fiscalyear')
    >>> Sequence = Model.get('ir.sequence')
    >>> SequenceStrict = Model.get('ir.sequence.strict')
    >>> fiscalyear = FiscalYear(name='%s' % today.year)
    >>> fiscalyear.start_date = today + relativedelta(month=1, day=1)
    >>> fiscalyear.end_date = today + relativedelta(month=12, day=31)
    >>> fiscalyear.company = company
    >>> post_move_sequence = Sequence(name='%s' % today.year,
    ...     code='account.move',
    ...     company=company)
    >>> post_move_sequence.save()
    >>> fiscalyear.post_move_sequence = post_move_sequence
    >>> invoice_sequence = SequenceStrict(name='%s' % today.year,
    ...     code='account.invoice',
    ...     company=company)
    >>> invoice_sequence.save()
    >>> fiscalyear.out_invoice_sequence = invoice_sequence
    >>> fiscalyear.in_invoice_sequence = invoice_sequence
    >>> fiscalyear.out_credit_note_sequence = invoice_sequence
    >>> fiscalyear.in_credit_note_sequence = invoice_sequence
    >>> fiscalyear.save()
    >>> FiscalYear.create_period([fiscalyear.id], config.context)

Create chart of accounts::

    >>> AccountTemplate = Model.get('account.account.template')
    >>> Account = Model.get('account.account')
    >>> AccountJournal = Model.get('account.journal')
    >>> account_template, = AccountTemplate.find([('parent', '=', None)])
    >>> create_chart = Wizard('account.create_chart')
    >>> create_chart.execute('account')
    >>> create_chart.form.account_template = account_template
    >>> create_chart.form.company = company
    >>> create_chart.execute('create_account')
    >>> receivable, = Account.find([
    ...     ('kind', '=', 'receivable'),
    ...     ('company', '=', company.id),
    ... ])
    >>> payable, = Account.find([
    ...     ('kind', '=', 'payable'),
    ...     ('company', '=', company.id),
    ... ])
    >>> revenue, = Account.find([
    ...     ('kind', '=', 'revenue'),
    ...     ('company', '=', company.id),
    ... ])
    >>> create_chart.form.account_receivable = receivable
    >>> create_chart.form.account_payable = payable
    >>> create_chart.execute('create_properties')

Create analytic accounts::

    >>> AnalyticAccount = Model.get('analytic_account.account')
    >>> root = AnalyticAccount(type='root', name='Root')
    >>> root.save()
    >>> analytic_account = AnalyticAccount(root=root, parent=root,
    ...     name='Sale Goal')
    >>> analytic_account.save()

Create parties and employees::

    >>> Employee = Model.get('company.employee')
    >>> party = Party(name='Party')
    >>> party.save()
    >>> employee_party = Party(name='Employee')
    >>> employee_party.save()
    >>> employee = Employee()
    >>> employee.party = employee_party
    >>> employee.company = company
    >>> employee.save()

Create a distribution with three lines::

    >>> Distribution = Model.get('sale.goal.distribution')
    >>> distribution = Distribution(name='Distribution')
    >>> line = distribution.lines.new()
    >>> line.name = 'First'
    >>> line.value = Decimal('25.0')
    >>> line = distribution.lines.new()
    >>> line.name = 'Second'
    >>> line.value = Decimal('25.0')
    >>> line = distribution.lines.new()
    >>> line.name = 'Third'
    >>> line.value = Decimal('50.0')
    >>> distribution.save()
    >>> distribution.total
    Decimal('100.0')

Create a goal::

    >>> Goal = Model.get('sale.goal')
    >>> goal = Goal()
    >>> goal.employee = employee
    >>> goal.party = party
    >>> goal.account = analytic_account
    >>> goal.amount = Decimal('1000.0')
    >>> goal.distribution = distribution
    >>> lines = dict((l.name, l.value) for l in goal.lines)
    >>> lines['First']
    Decimal('250.00')
    >>> lines['Second']
    Decimal('250.00')
    >>> lines['Third']
    Decimal('500.00')
    >>> goal.amount = Decimal('2000.0')
    >>> lines = dict((l.name, l.value) for l in goal.lines)
    >>> lines['First']
    Decimal('500.00')
    >>> lines['Second']
    Decimal('500.00')
    >>> lines['Third']
    Decimal('1000.00')

Change lines and distribution must be cleared::

    >>> goal.distribution == distribution
    True
    >>> for line in goal.lines:
    ...     line.value -= Decimal('100')
    >>> line = goal.lines.new()
    >>> line.name = 'Fourth'
    >>> line.value = Decimal('300')
    >>> goal.distribution
    >>> goal.save()





