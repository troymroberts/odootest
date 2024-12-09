# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from .chatter_fields_mapper import website_chatter_fields_dict


class WebsiteChatterFields(models.Model):
    _name = 'website.chatter.fields'
    _description = 'Website Chatter Field'

    FIELDS_TO_IGNORE = ['id', 'website_ids', 'data_html', 'display_name', 'create_uid',
                        'create_date', 'write_uid', 'write_date', 'width_suffix', 'height_suffix']

    # Fields for data to be embedded
    data_embed_id = fields.Char(string='Data Embed ID', required=True)
    data_greeting = fields.Char(string='Greeting')
    data_no_sponsor = fields.Char(string="No Sponsor")
    data_sponsor_link = fields.Char(string="Sponsor Link")
    data_sponsor_text = fields.Char(string="Sponsor Text")
    src = fields.Char(string='Source', required=True)
    data_assistant_name = fields.Char(string="Assistant Name")
    data_username = fields.Char(string='Username')
    data_support_email = fields.Char(string='Support Email')
    data_default_message = fields.Char(string="Default Message",
                                       help="Comma-separated messages displayed when the chat widget has no history. Example: 'How are you?', 'What is so interesting about this project?', 'Tell me a joke.'")

    # Measure Fields
    data_window_height = fields.Integer(string='Window Height')
    height_suffix = fields.Selection(
        [("px", "px"), ("%", "%"), ("rem", "rem")], default="px")
    data_window_width = fields.Integer(string='Window Width')
    width_suffix = fields.Selection(
        [("px", "px"), ("%", "%"), ("rem", "REM")], default="px")
    data_text_size = fields.Integer(string='Text Size')

    # Data URL Fields
    data_base_api_url = fields.Char(string="Base API URL", required=True)
    data_brand_image_url = fields.Char(string="Brand Image URL")

    data_chat_icon = fields.Selection([
        ("plus", "Plus"), ("chatBubble", "Chat Bubble"), 
        ("support", "Support"), ("search2", "Search2"),
        ("search", "Search"), ("magic", "Magic")
    ], string='Chat Icon', default="chatBubble")
    
    data_position = fields.Selection([
        ("bottom_right", "Bottom Right"), ("bottom_left", "Bottom Left"),
        ("top_right", "Top Right"), ("top_left", "Top Left")
    ], string='Position', default="bottom_right")

    data_html = fields.Html(string='Script Tag Content for Chatter Fields', sanitize=False)

    # Data-color Fields
    data_button_color = fields.Char(string='Button Color', default='#711919')
    data_user_bg_color = fields.Char(string='User Background Color', default='#711919')
    data_assistant_bg_color = fields.Char(string='Assistant Background Color', default='#711919')

    # Decision Making Fields (Boolean)
    data_open_on_load = fields.Boolean(string="Open On Load", default=False)

    # Many2one field to choose website to apply style for
    website_ids = fields.Many2one('website', string='Website to Apply Chatter')
    
    @api.model
    def create(self, vals):
    # Check if the current user already has a record
        existing_record = self.search_count([])
        if existing_record:
            raise UserError("You cannot create more than one record.")

        return super(WebsiteChatterFields, self).create(vals)

    @api.onchange(
        'data_embed_id', 'data_base_api_url', 'data_chat_icon', 'src', 'data_button_color',
        'data_assistant_bg_color', 'data_assistant_name', 'data_brand_image_url', 'data_default_message', 
        'data_greeting', 'data_no_sponsor', 'data_open_on_load', 'data_position', 'data_sponsor_link', 
        'data_sponsor_text', 'data_support_email', 'data_text_size', 'data_user_bg_color', 'data_username', 
        'data_window_height', 'data_window_width', 'height_suffix', 'width_suffix'
    )
    def _update_html_field(self):
        for record in self:
            record.data_html = self._generate_html_content(record)

    @api.model
    def _generate_html_content(self, record):
        content_string = "<script"
        for key, val in self._fields.items():
            if key in self.FIELDS_TO_IGNORE:
                continue
            else:
                value = getattr(record, key)
                if key == "data_window_width":
                    if value:
                        content_string += f'\n\t{website_chatter_fields_dict[key]}="{value}{record.width_suffix}"'
                elif key == "data_window_height":
                    if getattr(record, key):
                        content_string += f'\n\t{website_chatter_fields_dict[key]}="{value}{record.height_suffix}"'
                elif key == "data_open_on_load":
                    if value:
                        content_string += f'\n\t{website_chatter_fields_dict[key]}="on"'
                    else:
                        content_string += f'\n\t{website_chatter_fields_dict[key]}="off"'
                elif key == "data_text_size":
                        content_string += f'\n\t{website_chatter_fields_dict[key]}="{value}px"'
                elif key == "data_chat_icon" or key == "data_position":
                    content_string += f'\n\t{website_chatter_fields_dict[key]}="{self._get_selection_display_name(record, key)}"'
                elif value:
                    content_string += f'\n\t{website_chatter_fields_dict[key]}="{value}"'
               
        content_string += ">\n</script>"
        return content_string

    def _get_attribute_name(self, field_name):
        """Returns the string attribute for a field."""
        field = self._fields.get(field_name)
        return field.string if field and field_name not in self.FIELDS_TO_IGNORE else None

    def _get_selection_display_name(self, record, field_name):
        """Returns the display name of a selection field."""
        return dict(self._fields[field_name].selection).get(record[field_name], "")

    def action_sync(self):
        """Syncs the custom code footer for the selected website."""
        if self.website_ids:
            pages = self.env['website.page'].search([('website_published', "=", True)])
            for page in pages:
                if page.website_id == self.website_ids:
                    self.website_ids.custom_code_footer = self.data_html
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
