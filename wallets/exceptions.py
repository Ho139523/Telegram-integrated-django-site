# wallets/exceptions.py


class WalletError(Exception):
    """
    Base class for all wallet exceptions.
    """


class InvalidAmount(WalletError):
    pass


class InsufficientBalance(WalletError):
    pass


class InsufficientLockedBalance(WalletError):
    pass


class InsufficientPendingBalance(WalletError):
    pass


class DuplicateOperation(WalletError):
    pass


class SameWalletTransfer(WalletError):
    pass


class WithdrawalAlreadyProcessed(WalletError):
    pass


class WithdrawalNotPending(WalletError):
    pass


class CurrencyConversionNotFound(WalletError):
    pass

class InvalidCommission(ValueError):
    pass
