import collections

# Fix para MutableSet (Python 3.11+)
if not hasattr(collections, "MutableSet"):
    from collections.abc import MutableSet
    collections.MutableSet = MutableSet

# Fix para MutableMapping (Python 3.11+)
if not hasattr(collections, "MutableMapping"):
    from collections.abc import MutableMapping
    collections.MutableMapping = MutableMapping

# Fix para MutableSequence (só por segurança)
if not hasattr(collections, "MutableSequence"):
    from collections.abc import MutableSequence
    collections.MutableSequence = MutableSequence
    
import httpx

BASE_URL = "https://web.pirateswap.com/inventory/ExchangerInventory"

async def fetch_items(subcategories: list[str]):
    items = []

    async with httpx.AsyncClient() as client:
        for sub in subcategories:
            url = f"{BASE_URL}?orderBy=price&sortOrder=ASC&page=1&results=40&subcategory={sub}"
            r = await client.get(url, timeout=10)
            data = r.json()
            items.extend(data.get("items", []))

    return items
