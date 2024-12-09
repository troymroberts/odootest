/** @odoo-module **/

import { loadJS } from '@web/core/assets';
import { _t } from '@web/core/l10n/translation';
import publicWidget from '@web/legacy/js/public/public_widget';
import { Component } from "@odoo/owl";

publicWidget.registry.WiPayForm = publicWidget.Widget.extend({
    selector: '.o_wipay_form',
    events: {
        'click .wipay-submit-button': '_onSubmit',
        'change .wipay-payment-option': '_onPaymentOptionChange',
        'input .wipay-amount-input': '_onAmountChange',
        'click .wipay-save-card': '_onSaveCardChange'
    },

    start: async function () {
        await this._super.apply(this, arguments);
        this.paymentProvider = this.el.dataset.paymentProvider;
        this.redirectUrl = this.el.dataset.redirectUrl;
        this.amount = parseFloat(this.el.dataset.amount || '0');
        this.currency = this.el.dataset.currency;
        this.feeStructure = this.el.dataset.feeStructure;
        
        this._updateFeeDisplay();
        return this._initializeForm();
    },

    _initializeForm: async function () {
        // Add loading state
        this.el.classList.add('o_loading');
        
        try {
            // Initialize form elements
            await this._setupFormElements();
            
            // Handle saved cards if tokenization is enabled
            if (this.el.dataset.tokenizationEnabled === 'true') {
                await this._loadSavedCards();
            }
        } catch (error) {
            this._displayError(_t("Failed to initialize payment form"));
            console.error(error);
        } finally {
            this.el.classList.remove('o_loading');
        }
    },

    _setupFormElements: async function () {
        // Add required fields based on configuration
        const formContainer = this.el.querySelector('.wipay-form-container');
        if (!formContainer) return;

        // Clear existing content
        formContainer.innerHTML = '';

        // Add basic form structure
        const formHtml = `
            <div class="mb-3">
                <label class="form-label">${_t("Payment Amount")}</label>
                <div class="input-group">
                    <span class="input-group-text">${this.currency}</span>
                    <input type="text" class="form-control wipay-amount-input" 
                           value="${this.amount.toFixed(2)}" 
                           ${this.amount ? 'readonly' : ''}>
                </div>
                ${this.feeStructure !== 'merchant_absorb' ? `
                    <div class="fee-display text-muted small mt-1">
                        <span class="fee-amount"></span>
                        <span class="total-amount"></span>
                    </div>
                ` : ''}
            </div>
            
            ${this.el.dataset.tokenizationEnabled === 'true' ? `
                <div class="mb-3 saved-cards-section d-none">
                    <label class="form-label">${_t("Saved Cards")}</label>
                    <select class="form-select wipay-saved-cards"></select>
                </div>
            ` : ''}
            
            <div class="mb-3">
                <button type="button" class="btn btn-primary wipay-submit-button">
                    ${_t("Pay Now")}
                </button>
            </div>
        `;
        
        formContainer.innerHTML = formHtml;
    },

    _loadSavedCards: async function () {
        try {
            const response = await this._rpc({
                route: '/payment/wipay/get_saved_cards',
                params: {
                    'partner_id': parseInt(this.el.dataset.partnerId)
                }
            });
            
            if (response.cards && response.cards.length > 0) {
                const selectElement = this.el.querySelector('.wipay-saved-cards');
                selectElement.innerHTML = `
                    <option value="">${_t("Pay with a new card")}</option>
                    ${response.cards.map(card => `
                        <option value="${card.id}">
                            ${card.card_type} ****${card.last4} (${card.expiry})
                        </option>
                    `).join('')}
                `;
                this.el.querySelector('.saved-cards-section').classList.remove('d-none');
            }
        } catch (error) {
            console.error('Failed to load saved cards:', error);
        }
    },

    _updateFeeDisplay: function () {
        if (this.feeStructure === 'merchant_absorb') return;

        const feeDisplay = this.el.querySelector('.fee-display');
        if (!feeDisplay) return;

        this._rpc({
            route: '/payment/wipay/calculate_fees',
            params: {
                amount: this.amount,
                currency: this.currency
            }
        }).then(result => {
            if (result.success) {
                const feeAmount = parseFloat(result.fee_amount);
                const totalAmount = this.amount + (
                    this.feeStructure === 'customer_pay' ? feeAmount : feeAmount / 2
                );
                
                feeDisplay.querySelector('.fee-amount').textContent = 
                    _t("Fee: %s %s", this.currency, feeAmount.toFixed(2));
                feeDisplay.querySelector('.total-amount').textContent = 
                    _t("Total: %s %s", this.currency, totalAmount.toFixed(2));
            }
        }).catch(error => {
            console.error('Failed to calculate fees:', error);
        });
    },

    _onSubmit: async function (ev) {
        ev.preventDefault();
        const submitButton = ev.currentTarget;
        submitButton.setAttribute('disabled', 'disabled');
        
        try {
            // Get form data
            const formData = this._getFormData();
            
            // Validate data
            if (!this._validateFormData(formData)) {
                return;
            }
            
            // Process payment
            const result = await this._processPayment(formData);
            
            if (result.success) {
                window.location.href = result.redirect_url;
            } else {
                this._displayError(result.error || _t("Payment processing failed"));
            }
        } catch (error) {
            this._displayError(_t("An error occurred while processing your payment"));
            console.error(error);
        } finally {
            submitButton.removeAttribute('disabled');
        }
    },

    _validateFormData: function (formData) {
        // Add validation logic
        if (!formData.amount || formData.amount <= 0) {
            this._displayError(_t("Please enter a valid amount"));
            return false;
        }
        return true;
    },

    _getFormData: function () {
        return {
            amount: this.amount,
            currency: this.currency,
            saved_card_id: this.el.querySelector('.wipay-saved-cards')?.value || false,
            save_card: this.el.querySelector('.wipay-save-card')?.checked || false
        };
    },

    _processPayment: async function (formData) {
        return await this._rpc({
            route: '/payment/wipay/process_payment',
            params: formData
        });
    },

    _displayError: function (message) {
        const errorElement = this.el.querySelector('.wipay-error');
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.classList.remove('d-none');
        }
    },

    _onPaymentOptionChange: function (ev) {
        // Handle payment option changes
    },

    _onAmountChange: function (ev) {
        this.amount = parseFloat(ev.target.value || '0');
        this._updateFeeDisplay();
    },

    _onSaveCardChange: function (ev) {
        // Handle save card checkbox changes
    }
});

export default publicWidget.registry.WiPayForm;