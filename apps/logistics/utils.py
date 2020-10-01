from decimal import Decimal

from oscar_accounts.models import Account, AccountType, Transaction
from oscar_accounts import facade

from apps.users.models import User


def get_staff_account(user):
    acc_type_name = "Delivery Boy's COD Account"
    acc_type_code = "delivery_cod_intermediate_account"

    assert user.status in ['delivery_boy', 'request_pending'], \
        "Requested for Delivery Boy's wallet, but given Normal User"

    acc_type = AccountType.objects.filter(code=acc_type_code).first()
    if acc_type is None:
        acc_type = AccountType.add_root(code=acc_type_code, name=acc_type_name)
    staff_account, _ = Account.objects.get_or_create(
        primary_user=user, account_type=acc_type,
        defaults={'name': f"{user.get_full_name()} Wallet {user.id}", 'credit_limit': None})
    return staff_account


def get_anonymous_account():
    acc_type_name = "Generic Customer COD Account"
    acc_type_code = "common_customer_cod_debit_account"

    acc_type = AccountType.objects.filter(code=acc_type_code).first()
    if acc_type is None:
        acc_type = AccountType.add_root(code=acc_type_code, name=acc_type_name)
    anonymous_customer_account, _ = Account.objects.get_or_create(
        primary_user=None, account_type=acc_type, name='Customer',
        defaults={'description': f"Anonymous Customer Wallet",  'credit_limit': None})
    return anonymous_customer_account


def get_owner_account():
    acc_type_name = "Owner's Account"
    acc_type_code = "owners_account"

    acc_type = AccountType.objects.filter(code=acc_type_code).first()
    if acc_type is None:
        acc_type = AccountType.add_root(code=acc_type_code, name=acc_type_name)
    owner_account, _ = Account.objects.get_or_create(
        primary_user=None, account_type=acc_type, name='Admin',
        defaults={'description': f"Admin Wallet",  'credit_limit': None})
    return owner_account


class TransferCOD:
    from_account = None
    to_account = None

    def __init__(self, authorized_by: User,):
        self.authorized_by = authorized_by

    def from_staff(self, staff: User):
        self.from_account = get_staff_account(staff)
        return self

    def from_customer(self):
        self.from_account = get_anonymous_account()
        return self

    def from_admin(self):
        self.from_account = get_owner_account()
        return self

    def to_staff(self, staff: User,):
        self.to_account = get_staff_account(staff)
        return self

    def to_customer(self):
        self.to_account = get_anonymous_account()
        return self

    def to_admin(self):
        self.to_account = get_owner_account()
        return self

    def transfer(self, amount: Decimal, description=""):
        return facade.transfer(self.from_account, self.to_account, amount=amount,
                               user=self.authorized_by, description=description)

    def get_my_transactions(self):
        return self.authorized_by.transfers.all()

#