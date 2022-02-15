import json
import sys
import traceback
import re
from datetime import datetime
from urllib.parse import urljoin, urlunsplit

import requests
from flask import render_template, request, Blueprint, flash, current_app
from flask_admin import Admin, expose
from flask_admin.actions import action
from flask_admin.contrib.sqla import ModelView

import helpers as h
import processor
import persistence


db = persistence.db
bp = Blueprint('payment', __name__)


@bp.route('/', methods=["GET"])
def index():
    url = request.args.get('url', 'verygoodsecurity.com')
    return render_template('payment.html', url=url)


@bp.route('/payment', methods=["POST"])
def create():
    imm = request.values
    dic = imm.to_dict(flat=True)
    payment_entry = Payment.from_dict(dic)
    db.session.add(payment_entry)
    db.session.commit()
    json_data = json.dumps(dic)
    print(json_data)
    return render_template('show_redacted.html', data=dic, url=dic['url'])


class ProxySetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    proxy_username = db.Column(db.String(100))
    proxy_password = db.Column(db.String(100))
    proxy_url = db.Column(db.String(255))
    proxy_port = db.Column(db.String(5))
    active = db.Column(db.Boolean, default=False)

    @staticmethod
    def proxy_env_variables_present(config):
        return 'VGS_PROXY_URL' in config

    @classmethod
    def from_config(cls, config):
        proxy_setting = cls()
        proxy_setting.proxy_username = config['VGS_PROXY_USERNAME']
        proxy_setting.proxy_password = config['VGS_PROXY_PASSWORD']
        proxy_setting.proxy_url = config['VGS_PROXY_URL']
        proxy_setting.proxy_port = config['VGS_PROXY_PORT']
        proxy_setting.active = False
        return proxy_setting

    def as_dict(self):
        return {scheme: urlunsplit(
                (scheme,
                 '{PROXY_USERNAME}:{PROXY_PASSWORD}@{PROXY_URL}:{PROXY_PORT}'.format(
                     PROXY_USERNAME=self.proxy_username,
                     PROXY_PASSWORD=self.proxy_password,
                     PROXY_URL=self.proxy_url,
                     PROXY_PORT=self.proxy_port,
                 ),
                 '', None, None)) for scheme in ['https', 'http']}


def strip_scheme(target, value, oldvalue, initiator):
    """Strip scheme from url"""

    pattern = r'^(http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)?'
    return re.sub(pattern, '', value)

# setup listener on ProxySetting.proxy_url attribute, instructing
# it to use the return value
db.event.listen(ProxySetting.proxy_url, 'set', strip_scheme, retval=True)


class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    name = db.Column(db.String(100))
    billing_address = db.Column(db.String(100))
    card_number = db.Column(db.String(100))
    card_expiration = db.Column(db.String(100))
    card_security_code = db.Column(db.String(100))

    @classmethod
    def from_dict(cls, kwargs):
        payment_obj = cls()
        payment_obj.name = kwargs['name']
        payment_obj.billing_address = kwargs['billing_address']
        payment_obj.card_number = kwargs['card-number']
        payment_obj.card_expiration = kwargs['card-expiration-date']
        payment_obj.card_security_code = kwargs['card-security-code']
        return payment_obj

    def charge(self):
        response = _charge({
            'card': self.card_number,
            'card_expiration': self.card_expiration,
            'card_security_code': self.card_security_code,
            'amount': 10000})
        response.raise_for_status()
        print(response.json())
        return True


def _charge(payload, url=None):
    if not url:
        print(current_app.config)
        root_url = current_app.config['VGS_PROCESSOR_ROOT_URL']
        url = urljoin(root_url, '/charge')

    proxy_setting = ProxySetting.query.filter(ProxySetting.active == True).first()
    if not proxy_setting and ProxySetting.proxy_env_variables_present(current_app.config):
        proxy_setting = ProxySetting.from_config(current_app.config)

    proxies = proxy_setting.as_dict() if proxy_setting else None

    return requests.post(
        url,
        data=h.dumps(payload),
        headers={"Content-type": "application/json"},
        proxies=proxies,
        # you can find the equivalent cert in your dashboard
        #  under the "integration-docs" section
        verify='demo/static/vgs-sandbox.pem'
    )


class CustomView(ModelView):
    list_template = 'merchant/list.html'
    create_template = 'merchant/create.html'
    edit_template = 'merchant/edit.html'


class PaymentAdmin(CustomView):

    @action('charge', 'Charge', 'Are you sure you want to charge this card?')
    def action_charge(self, ids):
        try:
            query = Payment.query.filter(Payment.id.in_(ids))
            count = 0
            for payment_entry in query.all():
                payment_entry.charge()
                count += 1
            flash('{count} cards were charged successfully. '.format(count=count))
        except Exception as ex:
            print(''.join(traceback.format_exception(None, ex, ex.__traceback__)),
                  file=sys.stderr, flush=True)
            flash('Failed to approve users. {error}'.format(
                error=ex), category='error')


def init_app(app):
    app.register_blueprint(bp)
    merchant_admin = Admin(app,
                           url='/merchant_admin',
                           name='Merchant Portal',
                           base_template='merchant/layout.html',
                           template_mode='bootstrap2')
    merchant_admin.add_view(PaymentAdmin(
        Payment, db.session, endpoint='payments'))
    merchant_admin.add_view(CustomView(
        ProxySetting, db.session, endpoint='proxy_settings'))
    return app
