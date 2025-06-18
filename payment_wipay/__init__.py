# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from . import models
from . import controllers
from odoo import api, SUPERUSER_ID

from odoo.addons.payment import setup_provider, reset_payment_provider


def post_init_hook(env):
    setup_provider(env, 'wipay')


def uninstall_hook(env):
    reset_payment_provider(env, 'wipay')
