import collections

# Fix para Python 3.11
if not hasattr(collections, "MutableSet"):
    from collections.abc import MutableSet
    collections.MutableSet = MutableSet

if not hasattr(collections, "MutableMapping"):
    from collections.abc import MutableMapping
    collections.MutableMapping = MutableMapping

if not hasattr(collections, "MutableSequence"):
    from collections.abc import MutableSequence
    collections.MutableSequence = MutableSequence


import asyncio
from datetime import datetime
import httpx

from knife_tracker_backend.database import tokens_collection, assets_collection
from knife_tracker_backend.pirateswap import fetch_items_PirateSwap
from knife_tracker_backend.tradeit import fetch_items_TradeIt
from knife_tracker_backend.apns import send_apns_push


# ==========================================================
# USD → EUR converter
# ==========================================================
async def usd_to_eur(amount_usd: float) -> float:
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(
                "https://api.exchangerate.host/latest",
                params={"base": "USD", "symbols": "EUR"},
                timeout=5
            )
            eur = res.json()["rates"]["EUR"]
            return round(amount_usd * eur, 2)

    except:
        return round(amount_usd * 0.92, 2)


# ==========================================================
# Worker principal
# ==========================================================
async def run_worker():
    print("\n===============================")
    print("[WORKER] APNs iniciado!")
    print("===============================\n")

    while True:
        try:
            print("\n[WORKER] Novo ciclo iniciado...")

            devices = await tokens_collection.find().to_list(None)
            print(f"[WORKER] {len(devices)} dispositivos encontrados.")

            # Todas as armas de todos os devices
            weapons_to_fetch = {
                w
                for dev in devices
                if dev.get("notificationsEnabled", True)
                for w in dev["filters"]["categories"]
            }

            if not weapons_to_fetch:
                print("[WORKER] Sem categorias ativas. A dormir...")
                await asyncio.sleep(300)
                continue

            weapons_list = list(weapons_to_fetch)
            print("[WORKER] Armas a buscar:", weapons_list)

            # ---------- PIRATESWAP ----------
            pirate_items = await fetch_items_PirateSwap(weapons_list)
            print(f"[WORKER] PirateSwap → {len(pirate_items)} items")

            # ---------- TRADEIT ----------
            tradeit_items = await fetch_items_TradeIt(weapons_list)
            print(f"[WORKER] TradeIt → {len(tradeit_items)} items")

            # Juntar + marcar origem
            for p in pirate_items:
                p["source"] = "pirate"

            for t in tradeit_items:
                t["source"] = "tradeit"

            all_items = pirate_items + tradeit_items
            print(f"[WORKER] TOTAL items → {len(all_items)}\n")

            # ======================================================
            # PROCESSAR CADA ITEM
            # ======================================================
            for item in all_items:

                # Nome seguro (SEM NUNCA DAR NONE)
                item_name = (
                    item.get("name")
                    or item.get("marketHashName")
                    or "Unknown Item"
                )

                print("------------------------------------")
                print(f"[WORKER] ITEM → {item_name}")
                print("------------------------------------")

                item_id = item.get("id")
                if not item_id:
                    print("[WORKER] SKIP: item sem ID!")
                    continue

                price_eur = await usd_to_eur(item["price"])

                # Já existe?
                exists = await assets_collection.find_one({"_id": item_id})
                if exists:
                    print("[WORKER] Já existe na DB — ignorado.")
                    continue

                # Weapon
                weapon = item.get("weapon")
                if not weapon:
                    weapon = item_name.split("|")[0].replace("★", "").strip()

                # Inserir
                await assets_collection.insert_one({
                    "_id": item_id,
                    "weapon": weapon,
                    "float": item.get("float"),
                    "price": price_eur,
                    "createdAt": datetime.utcnow(),
                    "source": item["source"],
                    "img": item.get("img")
                })

                print(f"[WORKER] Guardado na DB → {item_id}")

                # ------------------------------------------------------
                # NOTIFICAÇÕES
                # ------------------------------------------------------
                for dev in devices:

                    if not dev.get("notificationsEnabled", True):
                        continue

                    apnsToken = dev.get("apnsToken")
                    if not apnsToken:
                        continue

                    filters = dev["filters"]
                    weapon_name = weapon.lower()

                    matches = any(f.lower() in weapon_name for f in filters["categories"])
                    if not matches:
                        continue

                    if filters.get("minPrice") and price_eur < filters["minPrice"]:
                        continue

                    if filters.get("maxPrice") and price_eur > filters["maxPrice"]:
                        continue

                    # Enviar notificação (AGORA COM O SITE)
                    await send_apns_push(
                        apnsToken,
                        title=f"New {weapon} ({item['source'].capitalize()})!",
                        body=f"{item_name} — €{price_eur}"
                    )

                    print("[WORKER] ✔ NOTIFICAÇÃO ENVIADA!")

            print("\n[WORKER] Ciclo completo. A esperar 5 minutos...\n")

        except Exception as e:
            print("\n[WORKER] ERRO GERAL NO CICLO:", e, "\n")

        await asyncio.sleep(600)
