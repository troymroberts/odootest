# Add to existing PaymentTransaction class

    def _get_specific_rendering_values(self, processing_values):
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'wipay':
            return res

        # Add AVS data if enabled
        if self.provider_id.wipay_enable_avs and self.partner_id:
            partner = self.partner_id
            res.update({
                'avs': '1',  # Enable AVS in WiPay request
                'addr1': partner.street or '',
                'addr2': partner.street2 or '',
                'city': partner.city or '',
                'state': partner.state_id.code if partner.state_id else '',
                'zipcode': partner.zip or '',
                'country': partner.country_id.code if partner.country_id else '',
                'phone': partner.phone or partner.mobile or '',
                'email': partner.email or '',
                'name': partner.name or '',
            })

        return res

    def _process_notification_data(self, notification_data):
        super()._process_notification_data(notification_data)
        if self.provider_code != 'wipay':
            return

        # Process AVS response if present
        avs_response = notification_data.get('avs_response')
        if avs_response and self.provider_id.wipay_enable_avs:
            if not self.provider_id._wipay_validate_avs_response(avs_response):
                self._set_error("Transaction declined due to address verification failure")
                return

        # Continue with normal processing...