// payment_wipay/static/src/js/payment_form.js
/** @odoo-module **/

import PaymentForm from '@payment/js/payment_form';

PaymentForm.include({
    /**
     * Override token flow if WiPay needs redirect-based handling.
     */
    _processTokenFlow(providerCode, paymentOptionId, paymentMethodCode, processingValues) {
        if (providerCode === 'wipay') {
            // Optional: log or debug
            console.log('Redirecting via WiPay with:', processingValues);

            // Example: open payment URL
            if (processingValues && processingValues.payment_url) {
                window.open(processingValues.payment_url, '_blank');
            } else {
                console.warn('WiPay payment_url missing in processingValues.');
            }

            return;
        }

        // fallback to default
        this._super(...arguments);
    },
});
