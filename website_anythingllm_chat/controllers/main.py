# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class LLMChatController(http.Controller):
    
    @http.route('/mail/chat/send_llm_message', type='json', auth='user')
    def send_llm_message(self, channel_id, message_id, message):
        try:
            result = request.env['mail.channel'].send_llm_message(
                int(channel_id),
                int(message_id),
                message
            )
            return {'success': result}
        except Exception as e:
            _logger.error("Error in send_llm_message controller: %s", str(e))
            return {'success': False, 'error': str(e)}