import collections

# Fix para MutableSet (Python 3.11+)
if not hasattr(collections, "MutableSet"):
    from collections.abc import MutableSet
    collections.MutableSet = MutableSet

# Fix para MutableMapping (Python 3.11+)
if not hasattr(collections, "MutableMapping"):
    from collections.abc import MutableMapping
    collections.MutableMapping = MutableMapping

# Fix para MutableSequence
if not hasattr(collections, "MutableSequence"):
    from collections.abc import MutableSequence
    collections.MutableSequence = MutableSequence

import httpx

BASE_URL = "https://tradeit.gg/api/v2/inventory/data"

async def fetch_items_TradeIt(subcategories: list[str]):
    items = []

    async with httpx.AsyncClient() as client:
        for sub in subcategories:
            params = {
                "gameId": 730,
                "sortType": "Price+-+low",
                "searchValue": sub,
                "type": 6,
                "showTradeLock": "true",
                "onlyTradeLock": "false",
                "showUserListing": "true",
                "context": "trade"
            }
            
            print(f"Fetching TradeIt for: {sub}")
            r = await client.get(BASE_URL, params=params, timeout=10)
            data = r.json()
            
            # Tenta diferentes estruturas possíveis
            raw_items = data.get("data", {}).get("items", [])
            if not raw_items:
                # Tenta estrutura alternativa
                raw_items = data.get("items", [])
                print(f"Trying alternative structure, items found: {len(raw_items)}")
            
            for item in raw_items:
                raw_price = item.get("sitePrice") or item.get("price") or 0
                price_usd = round(raw_price / 100, 2)
                
                items.append({
                    "id": str(item["id"]),
                    "name": item["name"],
                    "price": price_usd,
                    "img": item.get("imgURL")
                })
    return items