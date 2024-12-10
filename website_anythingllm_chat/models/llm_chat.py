# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests
import json
import logging

_logger = logging.getLogger(__name__)

class LLMChatMessage(models.Model):
    _name = 'llm.chat.message'
    _description = 'LLM Chat Message'
    _order = 'create_date asc'
    _rec_name = 'message'

    channel_id = fields.Many2one('mail.channel', string='Chat Channel', required=True, ondelete='cascade')
    message_id = fields.Many2one('mail.message', string='Related Message', ondelete='cascade')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    message = fields.Text(string='Message', required=True)
    response = fields.Text(string='LLM Response')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent to LLM'),
        ('received', 'Response Received'),
        ('error', 'Error')
    ], default='draft', string='Status')
    error_message = fields.Text(string='Error Details')

class MailChannel(models.Model):
    _inherit = 'mail.channel'

    is_llm_enabled = fields.Boolean('Enable LLM Chat', default=True)
    
    @api.model
    def send_llm_message(self, channel_id, message_id, message):
        channel = self.browse(channel_id)
        if not channel.is_llm_enabled:
            return False

        # Get API settings from system parameters
        ICP = self.env['ir.config_parameter'].sudo()
        api_url = ICP.get_param('llm_chat.api_url', False)
        api_key = ICP.get_param('llm_chat.api_key', False)

        if not api_url:
            raise UserError(_("LLM API URL not configured. Please configure it in Settings."))

        # Create LLM message record
        llm_message = self.env['llm.chat.message'].create({
            'channel_id': channel_id,
            'message_id': message_id,
            'message': message,
            'state': 'sent'
        })

        try:
            # Prepare headers
            headers = {
                'Content-Type': 'application/json'
            }
            if api_key:
                headers['Authorization'] = f'Bearer {api_key}'

            # Get conversation history
            history = self._get_chat_history(channel_id, limit=5)
            
            # Prepare payload
            payload = {
                'message': message,
                'history': history,
                'channel_id': channel_id,
            }

            # Send request to LLM API
            response = requests.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            llm_response = response.json().get('response', '')

            # Update LLM message record
            llm_message.write({
                'response': llm_response,
                'state': 'received'
            })

            # Send response back to chat channel
            self.env['mail.message'].create({
                'model': 'mail.channel',
                'res_id': channel_id,
                'message_type': 'comment',
                'body': llm_response,
                'author_id': self.env.ref('base.partner_root').id,
            })

            return True

        except Exception as e:
            _logger.error("Error sending message to LLM: %s", str(e))
            llm_message.write({
                'state': 'error',
                'error_message': str(e)
            })
            return False

    def _get_chat_history(self, channel_id, limit=5):
        """Get recent chat history for context"""
        messages = self.env['llm.chat.message'].search([
            ('channel_id', '=', channel_id),
            ('state', '=', 'received')
        ], limit=limit, order='create_date desc')
        
        history = []
        for msg in reversed(messages):
            history.extend([
                {'role': 'user', 'content': msg.message},
                {'role': 'assistant', 'content': msg.response}
            ])
        return history

    @api.model
    def create_channel(self, channel_type='chat', partners_to=None, email_send=False):
        channel = super().create_channel(channel_type=channel_type, partners_to=partners_to, email_send=email_send)
        if channel_type == 'chat':
            channel.write({'is_llm_enabled': True})
        return channel