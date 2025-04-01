import os
from yfinance import Ticker
from typing import Any, ClassVar, Self
from lunchable import LunchMoney
from lunchable.models import AssetsObject
from pydantic import BaseModel
from decimal import Decimal
import re
import logging

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class PricedAsset(BaseModel):
    """
    Represents an asset with a label, symbol, and quantity, and optionally a currency and price.
    The symbol needs to be available on Yahoo Finance: https://finance.yahoo.com/quote/<symbol>

    The asset string format is:
    "<label> [<symbol>]: <quantity>", e.g. "Apple [AAPL]: 10"
    "<label> [<symbol>]: <quantity> @ <currency> <price>", e.g. "Apple [AAPL]: 10 @ USD 100.00"
    """

    PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"^(?P<label>.*?)\s*\[(?P<symbol>.*?)\]:\s*(?P<quantity>[\d.]+?)(?:\s*@\s*(?P<currency>[A-Z]{3})\s*(?P<price>[\d.]+))?$")

    label: str
    symbol: str
    quantity: Decimal = Decimal(0)
    currency: str | None = None
    price: Decimal | None = None

    @property
    def value(self) -> Decimal | None:
        if self.price is None:
            return None
        return self.quantity * self.price

    @classmethod
    def from_string(cls, asset_string: str) -> Self:
        match = cls.PATTERN.match(asset_string)
        if not match:
            raise ValueError(f"Invalid asset string format: {asset_string}")

        return cls(
            label=match["label"],
            symbol=match["symbol"],
            quantity=Decimal(match["quantity"]) if match["quantity"] else Decimal(0),
            currency=match["currency"],
            price=Decimal(match["price"]) if match["price"] else None,
        )

    def load_price(self) -> None:
        ticker = Ticker(self.symbol)
        price_data: dict[str, Any] = ticker.info

        self.currency = price_data.get("currency", None)
        self.price = Decimal(price_data.get("regularMarketPrice", 0))

    def __str__(self) -> str:
        metadata = f" [{self.symbol}]: {self.quantity}"
        if self.price is not None:
            metadata += " @"
            if self.currency is not None:
                metadata += f" {self.currency}"
            metadata += f" {self.price:.2f}"

        max_length = 45 # Lunch Money API requirement
        label = self.label[:max_length - len(metadata)]
        return f"{label}{metadata}"

def update_asset_balance(lunch: LunchMoney, lm_asset: AssetsObject):
    name = lm_asset.name
    try:
        asset = PricedAsset.from_string(name)
    except ValueError:
        logger.debug(f"Not a priced asset: '{name}'")
        return

    try:
        asset.load_price()
    except Exception as e:
        logger.error(f"Error loading price for '{asset.label} [{asset.symbol}]': {e}")
        return

    try:
        # TODO: These can't actually be None/0 if the price was loaded successfully
        currency = asset.currency.lower() if asset.currency else None
        balance = float(asset.value or 0)

        lunch.update_asset(lm_asset.id, name=str(asset), currency=currency, balance=balance)
    except Exception as e:
        logger.error(f"Error updating asset '{asset.label} [{asset.symbol}]': {e}")
        return

    logger.info(f"{asset} = {asset.currency} {asset.value:.2f}")

def main():
    token = os.getenv("LUNCHMONEY_ACCESS_TOKEN")
    if not token:
        raise ValueError("LUNCHMONEY_ACCESS_TOKEN is not set")

    lunch = LunchMoney(access_token=token)
    lm_assets: list[AssetsObject] = lunch.get_assets()
    for lm_asset in lm_assets:
        update_asset_balance(lunch, lm_asset)

if __name__ == "__main__":
    main()
