from wallets.providers.zarinpal import (
    ZarinpalWithdrawalProvider,
)


class WithdrawalProviderFactory:

    _providers = {
        "zarinpal": ZarinpalWithdrawalProvider,
    }

    @classmethod
    def get(cls, provider: str):

        provider_class = cls._providers.get(provider)

        if provider_class is None:
            raise ValueError(
                f"Unsupported withdrawal provider: {provider}"
            )

        return provider_class()
