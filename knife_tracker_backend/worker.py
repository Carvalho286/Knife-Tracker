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


import asyncio
from datetime import datetime
from knife_tracker_backend.database import tokens_collection, assets_collection
from knife_tracker_backend.pirateswap import fetch_items
from knife_tracker_backend.apns import send_apns_push
import httpx


async def usd_to_eur(amount_usd: float) -> float:
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(
                "https://api.exchangerate.host/latest",
                params={"base": "USD", "symbols": "EUR"},
                timeout=5
            )
            eur = res.json()["rates"]["EUR"]
            print(f"[WORKER] Conversão USD→EUR: {amount_usd} → {round(amount_usd * eur, 2)}")
            return round(amount_usd * eur, 2)
    except Exception as e:
        print("[WORKER] Falha ao converter moeda, fallback usado. ERRO:", e)
        return round(amount_usd * 0.92, 2)


async def run_worker():
    print("\n===============================")
    print("[WORKER] APNs iniciado!")
    print("===============================\n")

    while True:
        try:
            print("\n[WORKER] Novo ciclo iniciado...")
            devices = await tokens_collection.find().to_list(None)

            print(f"[WORKER] {len(devices)} dispositivos encontrados.")

            # Armas a buscar (de todos os devices)
            weapons_to_fetch = {
                w
                for dev in devices
                if dev.get("notificationsEnabled", True)
                for w in dev["filters"]["categories"]
            }

            if not weapons_to_fetch:
                print("[WORKER] Sem categorias ativas. A dormir 5m.")
                await asyncio.sleep(300)
                continue

            print("[WORKER] Armas a buscar:", list(weapons_to_fetch))

            # Buscar items
            items = await fetch_items(list(weapons_to_fetch))
            print(f"[WORKER] {len(items)} items recebidos da API.\n")

            for item in items:
                print("------------------------------------")
                print(f"[WORKER] ITEM → {item.get('marketHashName')}")
                print("------------------------------------")

                item_id = item.get("id")
                if not item_id:
                    print("[WORKER] SKIP: item sem ID!")
                    continue

                price_eur = await usd_to_eur(item["price"])

                # Já existe?
                if await assets_collection.find_one({"_id": item_id}):
                    print("[WORKER] Já existe na DB — ignorado.")
                    continue

                # Inserir na DB
                await assets_collection.insert_one({
                    "_id": item_id,
                    "weapon": item["weapon"],
                    "float": item["float"],
                    "price": price_eur,
                    "createdAt": datetime.utcnow()
                })

                print(f"[WORKER] Guardado na DB → {item_id}")

                # Enviar notificações
                print("[WORKER] A verificar dispositivos...")

                for dev in devices:
                    if not dev.get("notificationsEnabled", True):
                        print("[WORKER] Device SKIP → notificações desativadas")
                        continue

                    apnsToken = dev.get("apnsToken")
                    if not apnsToken:
                        print("[WORKER] Device SKIP → não tem apnsToken")
                        continue

                    filters = dev["filters"]

                    # FILTROS
                    weapon_name = item["weapon"].lower()

                    # Verifica se algum filtro aparece no nome da arma
                    matches = any(f.lower() in weapon_name for f in filters["categories"])

                    if not matches:
                        print(f"[WORKER] SKIP → {item['weapon']} não corresponde a nenhum filtro {filters['categories']}.")
                        continue

                    if filters.get("minPrice") and item["price"] < filters["minPrice"]:
                        print("[WORKER] SKIP → preço abaixo do mínimo.")
                        continue

                    if filters.get("maxPrice") and item["price"] > filters["maxPrice"]:
                        print("[WORKER] SKIP → preço acima do máximo.")
                        continue

                    # ENVIAR NOTIFICAÇÃO
                    print(f"[WORKER] A ENVIAR APNs → {apnsToken}")

                    await send_apns_push(
                        apnsToken,
                        title=f"New {item['weapon']}!",
                        body=f"{item['marketHashName']} — €{price_eur}"
                    )

                    print("[WORKER] ✔ NOTIFICAÇÃO ENVIADA!")

            print("\n[WORKER] Ciclo completo. A esperar 5 minutos...\n")

        except Exception as e:
            print("\n[WORKER] ERRO GERAL NO CICLO:", e, "\n")

        await asyncio.sleep(300)
