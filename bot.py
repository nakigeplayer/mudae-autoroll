import os, time, json, requests, schedule
from datetime import datetime
import discum
from discum.utils.slash import SlashCommander

# Cargar variables de entorno
tokens = os.getenv("TOKENS", "").split(",")
server_ids = os.getenv("SERVER_IDS", "").split(",")
channel_ids = os.getenv("CHANNEL_IDS", "").split(",")
desiredChars = os.getenv("DESIRED_CHARS", "").split(",")
desiredSeries = os.getenv("DESIRED_SERIES", "").split(",")
desiredKakeras = ['kakeraP', 'kakeraO','kakeraR','kakeraW', 'kakeraL']
botID = '432610292342587392'

def rollSession(bot, token, channel_id, server_id, roll_command='mx', numbers_roll=14, roll_id=None):
    auth = {'authorization': token}
    url = f'https://discord.com/api/v8/channels/{channel_id}/messages'
    rollCommand = SlashCommander(bot.getSlashCommands(botID).json()).get([roll_command])

    print(f"\n🌀 Inicio sesión {roll_id} en canal {channel_id} ({numbers_roll} rolls)")
    claimed_once = False
    rolled_cards = []
    emoji = '👍'

    for i in range(1, numbers_roll + 1):
        bot.triggerSlashCommand(botID, channel_id, server_id, data=rollCommand)
        time.sleep(1.8)

        r = requests.get(url, headers=auth)
        jsonCard = json.loads(r.text)

        if not jsonCard or len(jsonCard[0].get('content', '')) != 0:
            continue

        data = jsonCard[0]
        embed = data.get('embeds', [{}])[0]
        cardName = embed.get('author', {}).get('name', 'null')
        description = embed.get('description', '')
        cardSeries = description.replace('\n', '**').split('**')[0]
        try:
            cardPower = int(description.split('**')[1])
        except (IndexError, ValueError):
            cardPower = 0
        is_claimed = 'footer' in embed and 'icon_url' in embed['footer']
        message_id = data['id']

        rolled_cards.append({
            'power': cardPower,
            'name': cardName,
            'series': cardSeries,
            'message_id': message_id,
            'claimed': is_claimed
        })

        match_series = any(cardSeries.lower().startswith(s.lower()) for s in desiredSeries)
        match_chars = cardName in desiredChars

        if not is_claimed and not claimed_once and (match_series or match_chars):
            requests.put(f"{url}/{message_id}/reactions/{emoji}/%40me", headers=auth)
            print(f"🔔 Claimed deseado: {cardName}")
            claimed_once = True

        # Reacción de kakera
        for comp in data.get("components", [])[0].get('components', []):
            emoji_data = comp.get('emoji', {})
            if emoji_data.get('name') in desiredKakeras:
                bot.click(data['author']['id'], channelID=channel_id, guildID=server_id,
                          messageID=data['id'], messageFlags=data['flags'],
                          data={'component_type': 2, 'custom_id': comp['custom_id']})
                print(f"💎 Kakera reaccionada: {emoji_data['name']} de {cardName}")
                time.sleep(0.5)

    # Si no se hizo claim, elegir la mejor opción no reclamada
    if not claimed_once:
        best_card = next((c for c in sorted(rolled_cards, key=lambda x: -x['power']) if not c['claimed']), None)
        if best_card:
            requests.put(f"{url}/{best_card['message_id']}/reactions/{emoji}/%40me", headers=auth)
            print(f"🎯 Claim por poder: {best_card['name']} ({best_card['power']})")
        else:
            print("⚠️ No se pudo hacer claim — todas las cards están reclamadas.")

    print(f"✅ Sesión {roll_id} finalizada.")

def startRollingSessions():
    for i, token in enumerate(tokens, start=1):
        bot = discum.Client(token=token, log=False)
        print(f"\n🚀 Iniciando sesiones con Token {i}")

        for j, channel_id in enumerate(channel_ids, start=1):
            server_id = server_ids[0]  # Tú decides manualmente cuál usar
            rollSession(
                bot=bot,
                token=token,
                channel_id=channel_id,
                server_id=server_id,
                roll_command='mx',
                numbers_roll=14,
                roll_id=f"{i}-{j}"
            )

        print(f"🏁 Token {i} completó todas sus sesiones.")

# Programar cada 3 horas
schedule.every(3).hours.do(startRollingSessions)

# Ejecutar indefinidamente
while True:
    schedule.run_pending()
    time.sleep(60)
