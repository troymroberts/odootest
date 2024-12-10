# -*- coding: utf-8 -*-
from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    llm_api_url = fields.Char(string='LLM API URL', config_parameter='llm_chat.api_url')
    llm_api_key = fields.Char(string='LLM API Key', config_parameter='llm_chat.api_key')
    llm_default_enabled = fields.Boolean(string='Enable LLM by Default', config_parameter='llm_chat.default_enabled')

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        if not self.env['ir.config_parameter'].sudo().get_param('llm_chat.api_url'):
            self.env['ir.config_parameter'].sudo().set_param('llm_chat.default_enabled', True)