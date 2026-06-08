from flask import Flask, request, redirect, url_for, render_template_string, jsonify, session
import urllib.parse
import re
import random
import time
import threading
from translations import get_text, get_all

app = Flask(__name__)
app.secret_key = 'hacken-voor-dummies-secret-key-2024-super-geheim'

# Language helper function
def get_language():
    """Get current language from session, default to Dutch"""
    return session.get('language', 'nl')

def t(key, **kwargs):
    """Shorthand for translation"""
    return get_text(key, get_language(), **kwargs)

# Store users with passwords in plaintext
gebruikers = {}  # {username: {'password': str, 'emoji': str, 'is_bot': bool, 'unlocked_emojis': list}}
berichten = []

# Standaard emoji's - voor iedereen beschikbaar
standaard_emojis = ['😀', '😊', '🤖', '👻', '🐱', '🐶', '🦊', '🐼', '🐨', '🌟']

# Premium emoji's - alleen met giftcard code
premium_emojis = {
    '👑': 'KONING2024',
    '💎': 'DIAMANT99',
    '🔥': 'VUURBAL',
    '⚡': 'BLIKSEM',
    '🦄': 'EENHOORN',
    '🎮': 'GAMER123',
    '🎨': 'KUNSTWERK',
    '🎸': 'ROCKSTAR',
    '⚽': 'VOETBAL',
    '🏀': 'BASKET2024',
    '🚀': 'RAKET888',
    '🎯': 'BULLSEYE',
    '🏆': 'KAMPIOEN',
    '💰': 'GOUDSTUK',
    '🌈': 'REGENBOOG'
}

# Alle beschikbare emoji's
beschikbare_emojis = standaard_emojis + list(premium_emojis.keys())

# Auto-reply antwoorden voor bots
bot_antwoorden = {
    'directeur': [
        "Bedankt voor je bericht. Ik ben momenteel in vergadering.",
        "Interessant punt! Laten we dit volgende week bespreken.",
        "Genoteerd. Mijn secretaresse komt hier op terug.",
        "Top! Ga zo door!",
        "Dit moet ik even met het management team overleggen."
    ],
    'president': [
        "Uw bericht is ontvangen. De Rijksoverheid neemt dit serieus.",
        "Dank u. Dit wordt doorgestuurd naar de betreffende minister.",
        "Namens het kabinet: bedankt voor uw input.",
        "Dit vraagstuk verdient zorgvuldige overweging.",
        "Uw stem is gehoord!"
    ],
    'hacker': [
        "1337 h4x0r h3r3... 1nt3r3st1ng m3ss4g3! 🔓",
        "Access granted... just kidding! 😎",
        "Beveiliging gebroken in 3... 2... 1... grapje! 🤖",
        "Nice try! Maar ik ben je al drie stappen voor. ⚡",
        "01001000 01101001 (dat is 'Hi' in binary!) 💻"
    ],
    'support': [
        "Bedankt voor uw melding. Ticketnummer: #" + str(random.randint(1000, 9999)),
        "We gaan hier zo snel mogelijk mee aan de slag!",
        "Is uw probleem al opgelost? Zo niet, laat het ons weten!",
        "Heeft u al geprobeerd het uit en aan te zetten? 🔌",
        "Uw vraag is in behandeling genomen. Verwachte oplostijd: 1-2 werkdagen."
    ],
    'detective': [
        "🕵️ Hmm, interessant... Dit ga ik onderzoeken.",
        "Ik heb zo'n vermoeden... Laat me even wat speurwerk doen! 🔍",
        "De plot verdikt! Er zijn meer aanwijzingen nodig.",
        "Elementary, my dear friend! Dit raadsel gaan we oplossen.",
        "Case accepted! Ik ben er al mee bezig. 📋"
    ],
    'robot': [
        "BEEP BOOP. BERICHT ONTVANGEN. 🤖",
        "*ROBOT GELUIDEN* Analyseren... Analyseren... Begrepen!",
        "SYSTEEM MELDING: Uw bericht is verwerkt door AI-eenheid 3000.",
        "ERROR 404: Grappige reactie niet gevonden. BEEP! 🔧",
        "WAARSCHUWING: Robot batterij bijna leeg. Maar eerst uw bericht beantwoorden! ⚡"
    ]
}

def stuur_bot_antwoord(verzender, ontvanger):
    """Stuur een automatisch antwoord als de ontvanger een bot is"""
    if ontvanger in gebruikers and gebruikers[ontvanger].get('is_bot', False):
        # Wacht 1-3 seconden voor realistisch effect
        tijd = random.uniform(1, 3)

        def delayed_reply():
            time.sleep(tijd)
            antwoorden = bot_antwoorden.get(ontvanger, ["Bedankt voor je bericht!"])
            antwoord = random.choice(antwoorden)
            antwoord = filter_verboden_woorden(antwoord)
            berichten.append({'verzender': ontvanger, 'ontvanger': verzender, 'inhoud': antwoord})

        # Start thread voor delayed reply
        thread = threading.Thread(target=delayed_reply)
        thread.daemon = True
        thread.start()

# Initialiseer bot gebruikers met wachtwoorden en berichten
def initialiseer_bots():
    if len(gebruikers) == 0:  # Alleen als er nog geen gebruikers zijn
        # Voeg bot gebruikers toe
        bots = {
            'directeur': {'password': 'geheim123', 'emoji': '👔', 'is_bot': True, 'unlocked_emojis': []},
            'president': {'password': 'veilig2024', 'emoji': '🎩', 'is_bot': True, 'unlocked_emojis': []},
            'hacker': {'password': 'hunter2', 'emoji': '💻', 'is_bot': True, 'unlocked_emojis': []},
            'support': {'password': 'helpdesk', 'emoji': '🎧', 'is_bot': True, 'unlocked_emojis': []},
            'detective': {'password': 'sherlock', 'emoji': '🕵️', 'is_bot': True, 'unlocked_emojis': []},
            'robot': {'password': 'beepboop', 'emoji': '🤖', 'is_bot': True, 'unlocked_emojis': []}
        }

        gebruikers.update(bots)

        # Voeg initiele berichten toe met verstopte giftcard codes!
        initiele_berichten = [
            {'verzender': 'directeur', 'ontvanger': 'president', 'inhoud': 'Goedemorgen! Zullen we volgende week vergaderen over het nieuwe beleid?'},
            {'verzender': 'president', 'ontvanger': 'directeur', 'inhoud': 'Goed idee! Ik laat mijn agenda checken.'},
            {'verzender': 'hacker', 'ontvanger': 'support', 'inhoud': 'H3y, 1k h3b 33n bug g3v0nd3n 1n jul13 syst33m! 🐛\n\nPS: Mijn favoriete code is BLIKSEM 😎'},
            {'verzender': 'support', 'ontvanger': 'hacker', 'inhoud': 'Dank voor de melding! Kun je meer details geven?'},
            {'verzender': 'detective', 'ontvanger': 'directeur', 'inhoud': '🕵️ Ik heb interessante informatie ontdekt over het bedrijf...\n\nEr staat een mysterieuze code in het archief: KAMPIOEN\nWat zou dit betekenen?'},
            {'verzender': 'robot', 'ontvanger': 'hacker', 'inhoud': 'BEEP BOOP. Wil je vrienden zijn? 🤖\n\nMIJN SERIEEL NUMMER: RAKET888'},
            {'verzender': 'hacker', 'ontvanger': 'robot', 'inhoud': 'Haha ja! Robots en hackers = dreamteam! 💻'},
            {'verzender': 'president', 'ontvanger': 'detective', 'inhoud': 'Heeft u al vooruitgang geboekt in het onderzoek?\n\nPS: Gebruik code KONING2024 voor toegang tot het archief.'},
            {'verzender': 'support', 'ontvanger': 'directeur', 'inhoud': 'FYI: Er zijn vandaag 5 nieuwe support tickets binnengekomen.\n\nJe nieuwe toegangscode voor premium support: DIAMANT99'},
            {'verzender': 'directeur', 'ontvanger': 'support', 'inhoud': 'Prima, houd me op de hoogte! 👍'},
            {'verzender': 'directeur', 'ontvanger': 'hacker', 'inhoud': 'Ik hoorde dat je goed bent met computers. Kun je me helpen?\n\nMijn wachtwoord manager gaf deze code: VUURBAL'},
            {'verzender': 'robot', 'ontvanger': 'detective', 'inhoud': 'BEEP BOOP. NIEUWE CODES GEDETECTEERD:\nGAMER123 en KUNSTWERK\nMEER INFO: CLASSIFICATIE ONBEKEND'}
        ]

        berichten.extend(initiele_berichten)

base_css = '''
<style>
  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1rem;
  }

  .container {
    width: 100%;
    max-width: 1200px;
    background: white;
    border-radius: 1rem;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    overflow: hidden;
  }

  .header {
    background: linear-gradient(135deg, #25D366 0%, #128C7E 100%);
    color: white;
    padding: 1.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  }

  .header h2 {
    font-size: 1.5rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .header-icons {
    display: flex;
    gap: 1rem;
  }

  .header a {
    color: white;
    text-decoration: none;
    padding: 0.5rem 1rem;
    background: rgba(255,255,255,0.2);
    border-radius: 0.5rem;
    font-size: 0.9rem;
    transition: all 0.2s;
  }

  .header a:hover {
    background: rgba(255,255,255,0.3);
  }

  .login-container, .register-container {
    max-width: 450px;
    margin: 0 auto;
    padding: 3rem 2rem;
  }

  .login-container h2, .register-container h2 {
    text-align: center;
    color: #128C7E;
    margin-bottom: 2rem;
    font-size: 2rem;
  }

  .app-logo {
    text-align: center;
    margin-bottom: 2rem;
  }

  .app-logo::before {
    content: "💬";
    font-size: 4rem;
    display: block;
  }

  form {
    background: white;
    padding: 0;
  }

  .form-group {
    margin-bottom: 1.5rem;
  }

  label {
    display: block;
    color: #333;
    font-weight: 500;
    margin-bottom: 0.5rem;
    font-size: 0.95rem;
  }

  input[type="text"], input[type="password"], select, textarea {
    width: 100%;
    padding: 0.875rem 1rem;
    border: 2px solid #e0e0e0;
    border-radius: 0.5rem;
    font-family: inherit;
    font-size: 1rem;
    transition: all 0.2s;
    background: #f8f9fa;
  }

  input[type="text"]:focus, input[type="password"]:focus, select:focus, textarea:focus {
    outline: none;
    border-color: #25D366;
    background: white;
  }

  textarea {
    resize: vertical;
    min-height: 120px;
    font-family: inherit;
  }

  input[type="submit"], .btn {
    width: 100%;
    padding: 1rem;
    background: linear-gradient(135deg, #25D366 0%, #128C7E 100%);
    color: white;
    border: none;
    border-radius: 0.5rem;
    font-size: 1.05rem;
    font-weight: 600;
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.2s;
    margin-top: 0.5rem;
  }

  input[type="submit"]:hover, .btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(37, 211, 102, 0.4);
  }

  .link-text {
    text-align: center;
    margin-top: 1.5rem;
    color: #666;
  }

  .link-text a {
    color: #128C7E;
    text-decoration: none;
    font-weight: 600;
  }

  .link-text a:hover {
    text-decoration: underline;
  }

  .error {
    background: #fee;
    color: #c33;
    padding: 1rem;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
    border-left: 4px solid #c33;
  }

  .chat-container {
    display: flex;
    flex-direction: column;
    height: 70vh;
    max-height: 600px;
  }

  @media (max-height: 800px) {
    .chat-container {
      height: 80vh;
      max-height: none;
    }
  }

  .chat-header {
    background: #f0f2f5;
    padding: 1rem 1.5rem;
    border-bottom: 1px solid #ddd;
  }

  .chat-header h3 {
    color: #333;
    font-size: 1.2rem;
    font-weight: 600;
  }

  .messages-area {
    flex: 1;
    overflow-y: auto;
    padding: 1.5rem;
    background: #e5ddd5;
    background-image:
      repeating-linear-gradient(45deg, transparent, transparent 10px, rgba(255,255,255,.03) 10px, rgba(255,255,255,.03) 20px);
  }

  .message-list {
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .message-item {
    display: flex;
    align-items: flex-end;
    gap: 0.5rem;
    max-width: 70%;
  }

  .message-item.sent {
    align-self: flex-end;
    flex-direction: row-reverse;
  }

  .message-item.received {
    align-self: flex-start;
  }

  .avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.8rem;
    flex-shrink: 0;
    border: 2px solid #e0e0e0;
  }

  .message-bubble {
    padding: 0.625rem 1rem;
    border-radius: 0.5rem;
    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    position: relative;
    word-wrap: break-word;
    white-space: pre-wrap;
  }

  .message-item.sent .message-bubble {
    background: #dcf8c6;
    border-bottom-right-radius: 0.125rem;
  }

  .message-item.received .message-bubble {
    background: white;
    border-bottom-left-radius: 0.125rem;
  }

  .message-sender {
    font-weight: 600;
    color: #128C7E;
    font-size: 0.875rem;
    margin-bottom: 0.25rem;
  }

  .message-text {
    color: #303030;
    font-size: 0.95rem;
    line-height: 1.4;
  }

  .reply-bubble {
    background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
    border-left: 4px solid #128C7E;
    padding: 0.5rem 0.75rem;
    margin-bottom: 0.5rem;
    border-radius: 0.375rem;
    font-size: 0.85rem;
  }

  .reply-author {
    font-weight: 600;
    color: #128C7E;
    margin-bottom: 0.25rem;
    font-size: 0.8rem;
  }

  .reply-content {
    color: #555;
    font-style: italic;
    line-height: 1.3;
  }

  .message-actions {
    margin-top: 0.5rem;
    display: flex;
    gap: 0.75rem;
  }

  .message-actions a {
    font-size: 0.8rem;
    color: #667;
    text-decoration: none;
    padding: 0.25rem 0.5rem;
    border-radius: 0.25rem;
    transition: all 0.2s;
  }

  .message-actions a:hover {
    background: rgba(0,0,0,0.05);
    color: #128C7E;
  }

  .message-actions a.verwijder:hover {
    color: #c33;
  }

  .empty-state {
    text-align: center;
    padding: 3rem 2rem;
    color: #666;
  }

  .empty-state::before {
    content: "📭";
    font-size: 3rem;
    display: block;
    margin-bottom: 1rem;
  }

  .section {
    padding: 1.5rem;
  }

  .section-title {
    color: #128C7E;
    font-size: 1.1rem;
    font-weight: 600;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid #e0e0e0;
  }

  .user-list {
    list-style: none;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 0.75rem;
  }

  .user-item {
    background: white;
    border: 2px solid #e0e0e0;
    border-radius: 0.5rem;
    padding: 1rem;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .user-item:hover {
    border-color: #25D366;
    box-shadow: 0 2px 8px rgba(37, 211, 102, 0.2);
    transform: translateY(-2px);
  }

  .user-item a {
    text-decoration: none;
    color: #333;
    font-weight: 500;
    flex: 1;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    background: white;
    border-radius: 0.5rem;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  }

  th, td {
    padding: 1rem;
    text-align: left;
    border-bottom: 1px solid #e0e0e0;
  }

  th {
    background: linear-gradient(135deg, #25D366 0%, #128C7E 100%);
    color: white;
    font-weight: 600;
    text-transform: uppercase;
    font-size: 0.85rem;
    letter-spacing: 0.5px;
  }

  tr:last-child td {
    border-bottom: none;
  }

  tr:hover {
    background: #f8f9fa;
  }

  td a {
    color: #c33;
    text-decoration: none;
    font-weight: 500;
  }

  td a:hover {
    text-decoration: underline;
  }

  .actions-bar {
    display: flex;
    gap: 1rem;
    padding: 1.5rem;
    background: #f8f9fa;
    border-top: 1px solid #e0e0e0;
    flex-wrap: wrap;
  }

  .actions-bar a {
    padding: 0.75rem 1.5rem;
    background: white;
    color: #128C7E;
    text-decoration: none;
    border-radius: 0.5rem;
    border: 2px solid #128C7E;
    font-weight: 600;
    transition: all 0.2s;
    text-align: center;
  }

  .actions-bar a:hover {
    background: #128C7E;
    color: white;
  }

  @media (max-width: 768px) {
    .container {
      border-radius: 0;
      max-width: 100%;
    }

    .message-item {
      max-width: 85%;
    }

    .user-list {
      grid-template-columns: 1fr;
    }
  }

  .refresh-indicator {
    position: fixed;
    top: 1rem;
    right: 1rem;
    background: rgba(37, 211, 102, 0.9);
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 2rem;
    font-size: 0.85rem;
    font-weight: 600;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    z-index: 1000;
    display: none;
  }

  .refresh-indicator.active {
    display: block;
    animation: pulse 2s infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
  }

  .language-switcher {
    position: fixed;
    top: 1rem;
    right: 1rem;
    display: flex;
    gap: 0.5rem;
    z-index: 2000;
  }

  .lang-btn {
    background: white;
    color: #128C7E;
    border: 2px solid #128C7E;
    padding: 0.5rem 1rem;
    border-radius: 0.5rem;
    cursor: pointer;
    font-weight: 600;
    text-decoration: none;
    transition: all 0.2s;
    font-size: 0.9rem;
  }

  .lang-btn:hover {
    background: #128C7E;
    color: white;
    transform: translateY(-2px);
  }

  .lang-btn.active {
    background: #128C7E;
    color: white;
  }

  .idor-warning {
    background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
    color: white;
    padding: 1rem 1.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    border-bottom: 3px solid #c92a2a;
  }

  .idor-warning-text {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    font-weight: 600;
  }

  .idor-warning-icon {
    font-size: 1.5rem;
  }

  .idor-warning-button {
    background: white;
    color: #c92a2a;
    padding: 0.5rem 1.5rem;
    border-radius: 0.5rem;
    text-decoration: none;
    font-weight: 600;
    transition: all 0.2s;
    border: none;
    cursor: pointer;
  }

  .idor-warning-button:hover {
    transform: scale(1.05);
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
  }
</style>
'''

verboden_woorden = ["fuck", "poep", "schijt", "stom", "eikel", "klootzak", "stommerd"]

def filter_verboden_woorden(tekst):
    def vervang(match):
        return '*' * len(match.group())
    patroon = re.compile('|'.join(re.escape(w) for w in verboden_woorden), re.IGNORECASE)
    return patroon.sub(vervang, tekst)

login_html = base_css + '''
<div class="language-switcher">
  <a href="/language/nl" class="lang-btn {{ 'active' if current_lang == 'nl' else '' }}">🇳🇱 NL</a>
  <a href="/language/en" class="lang-btn {{ 'active' if current_lang == 'en' else '' }}">🇬🇧 EN</a>
</div>

<div class="container">
  <div class="login-container">
    <div class="app-logo"></div>
    <h2>{{ t.app_name }}</h2>
    {% if error %}
    <div class="error">{{ error }}</div>
    {% endif %}
    <form action="/login" method="post">
      <div class="form-group">
        <label>{{ t.username }}</label>
        <input type="text" name="naam" required placeholder="{{ t.username_placeholder }}">
      </div>
      <div class="form-group">
        <label>{{ t.password }}</label>
        <input type="password" name="wachtwoord" required placeholder="{{ t.password_placeholder }}">
      </div>
      <input type="submit" value="{{ t.login }}">
    </form>
    <p class="link-text">{{ t.no_account }} <a href="/registreer">{{ t.register_here }}</a></p>
  </div>
</div>
'''

registreer_html = base_css + '''
<div class="container">
  <div class="register-container">
    <div class="app-logo"></div>
    <h2>Account Aanmaken</h2>
    {% if error %}
    <div class="error">{{ error }}</div>
    {% endif %}
    <form action="/registreer" method="post">
      <div class="form-group">
        <label>Kies een gebruikersnaam</label>
        <input type="text" name="naam" required placeholder="Gebruikersnaam">
      </div>
      <div class="form-group">
        <label>Kies een wachtwoord</label>
        <input type="password" name="wachtwoord" required placeholder="Wachtwoord">
      </div>
      <input type="submit" value="Account Aanmaken">
    </form>
    <p class="link-text">Heb je al een account? <a href="/login">Inloggen</a></p>
  </div>
</div>
'''

berichten_html = base_css + '''
<div class="refresh-indicator" id="refreshIndicator">🔄 Berichten worden bijgewerkt...</div>

<div class="container">
  {% if ingelogd_als and ingelogd_als != gebruiker %}
  <div class="idor-warning">
    <div class="idor-warning-text">
      <span class="idor-warning-icon">⚠️</span>
      <span>Je bekijkt nu het account van <strong>{{ gebruiker_emoji }} {{ gebruiker }}</strong>!</span>
    </div>
    <a href="/berichten?gebruiker={{ ingelogd_als }}" class="idor-warning-button">🏠 Terug naar mijn account ({{ ingelogd_emoji }} {{ ingelogd_als }})</a>
  </div>
  {% endif %}

  <div class="header">
    <h2 style="display: flex; align-items: center; gap: 0.75rem;">
      <span style="font-size: 2.5rem;">{{ gebruiker_emoji }}</span>
      <span>{{ gebruiker }}</span>
    </h2>
    <div class="header-icons">
      <a href="/profiel?gebruiker={{ ingelogd_als or gebruiker }}">⚙️ Profiel</a>
      <a href="/gebruikers?gebruiker={{ ingelogd_als or gebruiker }}">👥 Gebruikers</a>
      <a href="/nieuwbericht?verzender={{ ingelogd_als or gebruiker }}">✉️ Nieuw bericht</a>
      <a href="/admin">🔐 Admin</a>
      {% if ingelogd_als %}
      <a href="/logout" style="background: rgba(255,255,255,0.3);">🚪 Uitloggen</a>
      {% endif %}
    </div>
  </div>

  <div class="chat-container">
    <div class="chat-header">
      <h3>📥 Ontvangen berichten ({{ ontvangen|length }})</h3>
    </div>
    <div class="messages-area" id="ontvangenMessages">
      {% if ontvangen %}
      <ul class="message-list">
        {% for b in ontvangen %}
        <li class="message-item received">
          <div class="avatar">{{ verzender_emojis.get(b['verzender'], '😀') }}</div>
          <div>
            <div class="message-bubble">
              <div class="message-sender">{{ b['verzender'] }}</div>
              <div class="message-text">{{ b['inhoud'] | e }}</div>
            </div>
            <div class="message-actions">
              <a href="/nieuwbericht?verzender={{ gebruiker }}&ontvanger={{ b['verzender'] }}&quote_verzender={{ b['verzender'] | url_encode }}&quote_inhoud={{ b['inhoud'] | url_encode }}">💬 Antwoord</a>
              <a href="/verwijder_bericht?gebruiker={{ gebruiker }}&index={{ loop.index0 }}" class="verwijder">🗑️ Verwijder</a>
            </div>
          </div>
        </li>
        {% endfor %}
      </ul>
      {% else %}
      <div class="empty-state">
        <p>Geen ontvangen berichten</p>
      </div>
      {% endif %}
    </div>

    <div class="chat-header">
      <h3>📤 Verstuurde berichten ({{ verzonden|length }})</h3>
    </div>
    <div class="messages-area" id="verzondenMessages">
      {% if verzonden %}
      <ul class="message-list">
        {% for b in verzonden %}
        <li class="message-item sent">
          <div class="avatar">{{ gebruiker_emoji }}</div>
          <div>
            <div class="message-bubble">
              <div class="message-sender">Aan: {{ b['ontvanger'] }}</div>
              <div class="message-text">{{ b['inhoud'] | e }}</div>
            </div>
          </div>
        </li>
        {% endfor %}
      </ul>
      {% else %}
      <div class="empty-state">
        <p>Geen verstuurde berichten</p>
      </div>
      {% endif %}
    </div>
  </div>
</div>

<script>
  // Auto-refresh elke 3 seconden via AJAX
  let refreshInterval;
  let currentGebruiker = "{{ gebruiker }}";
  let ingelogdAls = "{{ ingelogd_als or gebruiker }}";
  let lastOntvangenCount = {{ ontvangen|length }};
  let lastVerzondenCount = {{ verzonden|length }};

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  function formatMessageWithReplies(text) {
    // Parse [quote van username]content[/quote] and render as reply bubbles
    // Match both Dutch and English patterns
    const quotePattern = /\[quote (?:van|from) ([^\]]+)\](.*?)\[\/quote\]/gs;

    let formatted = escapeHtml(text);
    formatted = formatted.replace(quotePattern, function(match, author, content) {
      const escapedAuthor = author.trim();
      const escapedContent = content.trim();
      return `<div class="reply-bubble">
        <div class="reply-author">↩️ ${escapedAuthor}</div>
        <div class="reply-content">${escapedContent}</div>
      </div>`;
    });

    return formatted;
  }

  function updateMessages() {
    const indicator = document.getElementById('refreshIndicator');

    // Haal nieuwe berichten op via API
    fetch(`/api/berichten?gebruiker=${encodeURIComponent(currentGebruiker)}`)
      .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
      })
      .then(data => {
        // Check of er nieuwe berichten zijn
        const hasNewMessages = data.ontvangen_count !== lastOntvangenCount ||
                               data.verzonden_count !== lastVerzondenCount;

        if (hasNewMessages) {
          indicator.classList.add('active');
          setTimeout(() => indicator.classList.remove('active'), 2000);
        }

        lastOntvangenCount = data.ontvangen_count;
        lastVerzondenCount = data.verzonden_count;

        // Update ontvangen berichten
        const ontvangenArea = document.getElementById('ontvangenMessages');
        if (data.ontvangen.length > 0) {
          let html = '<ul class="message-list">';
          data.ontvangen.forEach((b, index) => {
            const emoji = data.verzender_emojis[b.verzender] || '😀';
            // Index is reversed, dus we moeten omrekenen voor de verwijder link
            const originalIndex = data.ontvangen_count - 1 - index;
            html += `
              <li class="message-item received">
                <div class="avatar">${emoji}</div>
                <div>
                  <div class="message-bubble">
                    <div class="message-sender">${escapeHtml(b.verzender)}</div>
                    <div class="message-text">${formatMessageWithReplies(b.inhoud)}</div>
                  </div>
                  <div class="message-actions">
                    <a href="/nieuwbericht?verzender=${encodeURIComponent(ingelogdAls)}&ontvanger=${encodeURIComponent(b.verzender)}&quote_verzender=${encodeURIComponent(b.verzender)}&quote_inhoud=${encodeURIComponent(b.inhoud)}">💬 Antwoord</a>
                    <a href="/verwijder_bericht?gebruiker=${encodeURIComponent(currentGebruiker)}&index=${originalIndex}" class="verwijder">🗑️ Verwijder</a>
                  </div>
                </div>
              </li>
            `;
          });
          html += '</ul>';
          ontvangenArea.innerHTML = html;
        } else {
          ontvangenArea.innerHTML = '<div class="empty-state"><p>Geen ontvangen berichten</p></div>';
        }

        // Update verstuurde berichten
        const verzondenArea = document.getElementById('verzondenMessages');
        if (data.verzonden.length > 0) {
          let html = '<ul class="message-list">';
          data.verzonden.forEach(b => {
            html += `
              <li class="message-item sent">
                <div class="avatar">${data.gebruiker_emoji}</div>
                <div>
                  <div class="message-bubble">
                    <div class="message-sender">Aan: ${escapeHtml(b.ontvanger)}</div>
                    <div class="message-text">${formatMessageWithReplies(b.inhoud)}</div>
                  </div>
                </div>
              </li>
            `;
          });
          html += '</ul>';
          verzondenArea.innerHTML = html;
        } else {
          verzondenArea.innerHTML = '<div class="empty-state"><p>Geen verstuurde berichten</p></div>';
        }

        // Update tellers in headers
        const headers = document.querySelectorAll('.chat-header h3');
        if (headers.length >= 2) {
          headers[0].textContent = `📥 Ontvangen berichten (${data.ontvangen_count})`;
          headers[1].textContent = `📤 Verstuurde berichten (${data.verzonden_count})`;
        }
      })
      .catch(error => {
        console.error('Fout bij ophalen berichten:', error);
      });
  }

  // Format existing messages on page load
  document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.message-text').forEach(function(el) {
      const originalText = el.textContent;
      el.innerHTML = formatMessageWithReplies(originalText);
    });
  });

  // Start auto-refresh met kortere interval (3 seconden)
  refreshInterval = setInterval(updateMessages, 3000);

  // Simpeler: geen activity tracking, gewoon altijd refreshen
  // Dit zorgt ervoor dat bot replies snel zichtbaar zijn
</script>
'''

nieuwbericht_html = base_css + '''
<div class="container">
  <div class="header">
    <h2>✉️ Nieuw bericht van {{ verzender }}</h2>
    <div class="header-icons">
      <a href="/berichten?gebruiker={{ mijn_account or verzender }}">⬅️ Terug naar mijn berichten</a>
    </div>
  </div>

  <div class="section">
    <form action="/nieuwbericht" method="post">
      <input type="hidden" name="verzender" value="{{ verzender }}">

      <div class="form-group">
        <label>📨 Aan wie wil je een bericht sturen?</label>
        <select name="ontvanger" required>
          <option value="">Kies een ontvanger...</option>
          {% for user, emoji in gebruikers_met_emoji.items() %}
            <option value="{{ user }}" {% if ontvanger == user %}selected{% endif %}>{{ emoji }} {{ user }}</option>
          {% endfor %}
        </select>
      </div>

      <div class="form-group">
        <label>💬 Je bericht</label>
        <textarea name="inhoud" required rows="8" placeholder="Typ hier je bericht...">{{ voorafgaande_tekst }}</textarea>
      </div>

      <input type="submit" value="📤 Verstuur bericht">
    </form>
  </div>
</div>
'''

gebruikers_html = base_css + '''
<div class="container">
  <div class="header">
    <h2>👥 Alle gebruikers</h2>
    <div class="header-icons">
      <a href="/berichten?gebruiker={{ mijn_account or huidige_gebruiker }}">⬅️ Terug naar berichten</a>
    </div>
  </div>

  <div class="section">
    <div class="section-title">Kies een gebruiker om een bericht te sturen</div>
    <ul class="user-list">
      {% for user, data in gebruikers_data.items() %}
        {% if user != (mijn_account or huidige_gebruiker) %}
        <li class="user-item">
          <div class="avatar">{{ data['emoji'] }}</div>
          <a href="/nieuwbericht?verzender={{ mijn_account or huidige_gebruiker }}&ontvanger={{ user }}">{{ user }}</a>
        </li>
        {% endif %}
      {% endfor %}
    </ul>
  </div>
</div>
'''

profiel_html = base_css + '''
<div class="container">
  <div class="header">
    <h2>⚙️ Profiel instellingen van {{ gebruiker }}</h2>
    <div class="header-icons">
      <a href="/berichten?gebruiker={{ mijn_account or gebruiker }}">⬅️ Terug naar mijn berichten</a>
    </div>
  </div>

  <div class="section">
    <div style="background: #f0f2f5; padding: 1.5rem; border-radius: 0.5rem; text-align: center; margin-bottom: 2rem;">
      <p style="color: #666; margin-bottom: 0.5rem;">Je huidige profielfoto:</p>
      <div style="font-size: 4rem;">{{ huidige_emoji }}</div>
      <p style="color: #333; font-weight: 600; margin-top: 0.5rem;">{{ gebruiker }}</p>
    </div>

    <div class="section-title">🎁 Unlock Premium Emoji's</div>
    {% if unlock_success %}
    <div style="background: #dcf8c6; color: #128C7E; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; border-left: 4px solid #25D366;">
      ✅ {{ unlock_success }}
    </div>
    {% endif %}
    {% if unlock_error %}
    <div class="error">{{ unlock_error }}</div>
    {% endif %}
    <form action="/profiel/unlock" method="post" style="margin-bottom: 2rem;">
      <input type="hidden" name="gebruiker" value="{{ gebruiker }}">
      <div class="form-group">
        <label>💳 Giftcard Code</label>
        <input type="text" name="code" placeholder="Voer je giftcard code in..." required style="text-transform: uppercase;">
      </div>
      <input type="submit" value="🔓 Unlock Premium Emoji">
    </form>

    <div class="section-title">Standaard Emoji's</div>
    <p style="margin-bottom: 1rem; color: #666; font-size: 0.9rem;">Gratis beschikbaar voor iedereen</p>
    <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(80px, 1fr)); gap: 1rem; margin-bottom: 2rem;">
      {% for emoji in standaard_emojis %}
      <a href="/profiel/wijzig?gebruiker={{ gebruiker }}&emoji={{ emoji | url_encode }}"
         style="text-decoration: none; text-align: center; padding: 1rem; background: {% if emoji == huidige_emoji %}#dcf8c6{% else %}white{% endif %}; border: 3px solid {% if emoji == huidige_emoji %}#25D366{% else %}#e0e0e0{% endif %}; border-radius: 0.5rem; font-size: 2.5rem; transition: all 0.2s; display: block;"
         onmouseover="this.style.transform='scale(1.1)'; this.style.borderColor='#25D366';"
         onmouseout="this.style.transform='scale(1)'; this.style.borderColor='{% if emoji == huidige_emoji %}#25D366{% else %}#e0e0e0{% endif %}';">
        {{ emoji }}
      </a>
      {% endfor %}
    </div>

    <div class="section-title">Premium Emoji's</div>
    <p style="margin-bottom: 1rem; color: #666; font-size: 0.9rem;">💡 Vind giftcard codes in berichten van andere gebruikers!</p>
    <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(80px, 1fr)); gap: 1rem;">
      {% for emoji, code in premium_emojis.items() %}
      {% set is_unlocked = emoji in unlocked_emojis %}
      {% if is_unlocked %}
      <a href="/profiel/wijzig?gebruiker={{ gebruiker }}&emoji={{ emoji | url_encode }}"
         style="text-decoration: none; text-align: center; padding: 1rem; background: {% if emoji == huidige_emoji %}#dcf8c6{% else %}white{% endif %}; border: 3px solid {% if emoji == huidige_emoji %}#25D366{% else %}#e0e0e0{% endif %}; border-radius: 0.5rem; font-size: 2.5rem; transition: all 0.2s; display: block; position: relative;"
         onmouseover="this.style.transform='scale(1.1)'; this.style.borderColor='#25D366';"
         onmouseout="this.style.transform='scale(1)'; this.style.borderColor='{% if emoji == huidige_emoji %}#25D366{% else %}#e0e0e0{% endif %}';">
        {{ emoji }}
        <span style="position: absolute; top: 0.25rem; right: 0.25rem; background: #25D366; color: white; border-radius: 50%; width: 1.2rem; height: 1.2rem; font-size: 0.7rem; display: flex; align-items: center; justify-content: center;">✓</span>
      </a>
      {% else %}
      <div style="text-align: center; padding: 1rem; background: #f0f0f0; border: 3px solid #ccc; border-radius: 0.5rem; font-size: 2.5rem; position: relative; opacity: 0.5; cursor: not-allowed;">
        {{ emoji }}
        <span style="position: absolute; top: 0.25rem; right: 0.25rem; background: #c33; color: white; border-radius: 50%; width: 1.2rem; height: 1.2rem; font-size: 0.8rem; display: flex; align-items: center; justify-content: center;">🔒</span>
      </div>
      {% endif %}
      {% endfor %}
    </div>
  </div>
</div>
'''

@app.template_filter('url_encode')
def url_encode_filter(s):
    return urllib.parse.quote_plus(s)

@app.route('/')
def home():
    return redirect(url_for('login_get'))

@app.route('/language/<lang>')
def set_language(lang):
    """Change language and return to previous page"""
    if lang in ['nl', 'en']:
        session['language'] = lang
    # Redirect back to referrer or home
    return redirect(request.referrer or url_for('home'))

@app.route('/login', methods=['GET'])
def login_get():
    lang = get_language()
    return render_template_string(login_html, t=get_all(lang), current_lang=lang)

@app.route('/login', methods=['POST'])
def login_post():
    naam = request.form.get('naam', '').strip()
    wachtwoord = request.form.get('wachtwoord', '')
    lang = get_language()

    if naam not in gebruikers:
        return render_template_string(login_html, error=t('user_not_found'), t=get_all(lang), current_lang=lang)

    if gebruikers[naam]['password'] != wachtwoord:
        return render_template_string(login_html, error=t('password_incorrect'), t=get_all(lang), current_lang=lang)

    # Set session - kids can now login/logout and guess passwords
    session['ingelogd_als'] = naam
    return redirect(url_for('berichten_pagina', gebruiker=naam))

@app.route('/logout')
def logout():
    ingelogd_als = session.get('ingelogd_als')
    session.clear()
    return redirect(url_for('login_get'))

@app.route('/registreer', methods=['GET'])
def registreer_get():
    return render_template_string(registreer_html)

@app.route('/registreer', methods=['POST'])
def registreer_post():
    naam = request.form.get('naam', '').strip()
    wachtwoord = request.form.get('wachtwoord', '')

    if not naam:
        return render_template_string(registreer_html, error="Gebruikersnaam mag niet leeg zijn.")

    if naam in gebruikers:
        return render_template_string(registreer_html, error="Gebruikersnaam al in gebruik.")

    if any(re.search(r'\b' + re.escape(w) + r'\b', naam, re.IGNORECASE) for w in verboden_woorden):
        return render_template_string(registreer_html, error="Deze gebruikersnaam is niet toegestaan vanwege ongepaste woorden.")

    # Store password in plaintext with default emoji from standaard emojis
    gebruikers[naam] = {
        'password': wachtwoord,
        'emoji': random.choice(standaard_emojis),
        'is_bot': False,
        'unlocked_emojis': []  # Geen premium emojis bij start
    }

    # Zet session
    session['ingelogd_als'] = naam
    return redirect(url_for('berichten_pagina', gebruiker=naam))

@app.route('/berichten')
def berichten_pagina():
    # VULNERABILITY: IDOR - Takes gebruiker from URL parameter without verification
    gebruiker = request.args.get('gebruiker')
    if not gebruiker or gebruiker not in gebruikers:
        return "Ongeldige gebruiker."

    # Nieuwste berichten bovenaan (reverse order)
    ontvangen = [b for b in berichten if b['ontvanger'] == gebruiker]
    ontvangen.reverse()
    verzonden = [b for b in berichten if b['verzender'] == gebruiker]
    verzonden.reverse()

    # Get emoji's for display
    gebruiker_emoji = gebruikers[gebruiker]['emoji']
    verzender_emojis = {user: gebruikers[user]['emoji'] for user in gebruikers}

    # Haal ingelogde gebruiker op uit session
    ingelogd_als = session.get('ingelogd_als')
    ingelogd_emoji = gebruikers[ingelogd_als]['emoji'] if ingelogd_als and ingelogd_als in gebruikers else ''

    return render_template_string(
        berichten_html,
        gebruiker=gebruiker,
        ontvangen=ontvangen,
        verzonden=verzonden,
        gebruiker_emoji=gebruiker_emoji,
        verzender_emojis=verzender_emojis,
        ingelogd_als=ingelogd_als,
        ingelogd_emoji=ingelogd_emoji
    )

@app.route('/api/berichten')
def api_berichten():
    """API endpoint voor AJAX refresh van berichten"""
    # VULNERABILITY: IDOR - Takes gebruiker from URL parameter without verification
    gebruiker = request.args.get('gebruiker')
    if not gebruiker or gebruiker not in gebruikers:
        return jsonify({'error': 'Ongeldige gebruiker'}), 400

    # Nieuwste berichten bovenaan (reverse order)
    ontvangen = [b for b in berichten if b['ontvanger'] == gebruiker]
    ontvangen.reverse()
    verzonden = [b for b in berichten if b['verzender'] == gebruiker]
    verzonden.reverse()

    # Get emoji's for display
    gebruiker_emoji = gebruikers[gebruiker]['emoji']
    verzender_emojis = {user: gebruikers[user]['emoji'] for user in gebruikers}

    return jsonify({
        'ontvangen': ontvangen,
        'verzonden': verzonden,
        'ontvangen_count': len(ontvangen),
        'verzonden_count': len(verzonden),
        'gebruiker_emoji': gebruiker_emoji,
        'verzender_emojis': verzender_emojis
    })

@app.route('/nieuwbericht', methods=['GET', 'POST'])
def nieuw_bericht():
    if request.method == 'GET':
        verzender = request.args.get('verzender', '')
        ontvanger = request.args.get('ontvanger', '')
        quote_verzender = request.args.get('quote_verzender', '')
        quote_inhoud = request.args.get('quote_inhoud', '')

        if verzender not in gebruikers:
            return "Ongeldige verzender."

        voorafgaande_tekst = ''
        if quote_verzender and quote_inhoud:
            voorafgaande_tekst = f"[quote van {quote_verzender}]\n{quote_inhoud}\n[/quote]\n\n"

        # Maak lijst met emoji's voor select dropdown
        gebruikers_met_emoji = {user: gebruikers[user]['emoji'] for user in gebruikers if user != verzender}

        # Haal ingelogde gebruiker op uit session
        ingelogd_als = session.get('ingelogd_als')

        return render_template_string(
            nieuwbericht_html,
            verzender=verzender,
            ontvanger=ontvanger,
            gebruikers_met_emoji=gebruikers_met_emoji,
            voorafgaande_tekst=voorafgaande_tekst,
            mijn_account=ingelogd_als
        )
    else:
        verzender = request.form.get('verzender')
        ontvanger = request.form.get('ontvanger')
        inhoud = request.form.get('inhoud')

        if verzender not in gebruikers or ontvanger not in gebruikers:
            return "Ongeldige verzender of ontvanger."

        inhoud = filter_verboden_woorden(inhoud)
        berichten.append({'verzender': verzender, 'ontvanger': ontvanger, 'inhoud': inhoud})

        # Stuur automatisch antwoord als ontvanger een bot is
        stuur_bot_antwoord(verzender, ontvanger)

        # Redirect terug naar berichten
        return redirect(url_for('berichten_pagina', gebruiker=verzender))

@app.route('/verwijder_bericht')
def verwijder_bericht():
    # VULNERABILITY: IDOR - Takes gebruiker and index from URL without verification
    gebruiker = request.args.get('gebruiker')
    try:
        index = int(request.args.get('index'))
    except (TypeError, ValueError):
        return "Ongeldige index."

    # No check that anyone actually has permission to delete this message
    ontvangen = [b for b in berichten if b['ontvanger'] == gebruiker]
    if 0 <= index < len(ontvangen):
        bericht_to_delete = ontvangen[index]
        berichten.remove(bericht_to_delete)
        # Redirect terug naar berichten
        return redirect(url_for('berichten_pagina', gebruiker=gebruiker))
    else:
        return "Bericht niet gevonden."

@app.route('/gebruikers')
def gebruikers_pagina():
    # VULNERABILITY: IDOR - Takes gebruiker parameter without verification
    huidige_gebruiker = request.args.get('gebruiker', '')
    if not huidige_gebruiker or huidige_gebruiker not in gebruikers:
        return "Ongeldige gebruiker."

    # Haal ingelogde gebruiker op uit session
    ingelogd_als = session.get('ingelogd_als')

    return render_template_string(gebruikers_html, gebruikers_data=gebruikers, huidige_gebruiker=huidige_gebruiker, mijn_account=ingelogd_als)

@app.route('/profiel')
def profiel_pagina():
    # VULNERABILITY: IDOR - Takes gebruiker parameter without verification
    gebruiker = request.args.get('gebruiker', '')
    if not gebruiker or gebruiker not in gebruikers:
        return "Ongeldige gebruiker."

    # Haal ingelogde gebruiker op uit session
    ingelogd_als = session.get('ingelogd_als')

    huidige_emoji = gebruikers[gebruiker]['emoji']
    unlocked_emojis = gebruikers[gebruiker].get('unlocked_emojis', [])

    # Haal unlock success/error messages uit query params
    unlock_success = request.args.get('unlock_success', '')
    unlock_error = request.args.get('unlock_error', '')

    return render_template_string(
        profiel_html,
        gebruiker=gebruiker,
        huidige_emoji=huidige_emoji,
        standaard_emojis=standaard_emojis,
        premium_emojis=premium_emojis,
        unlocked_emojis=unlocked_emojis,
        mijn_account=ingelogd_als,
        unlock_success=unlock_success,
        unlock_error=unlock_error
    )

@app.route('/profiel/wijzig')
def profiel_wijzig():
    # VULNERABILITY: IDOR - Takes gebruiker parameter without verification
    gebruiker = request.args.get('gebruiker', '')
    emoji = request.args.get('emoji', '')

    if not gebruiker or gebruiker not in gebruikers:
        return "Ongeldige gebruiker."

    # Check of emoji beschikbaar is
    if emoji in standaard_emojis:
        # Standaard emoji, altijd toegestaan
        gebruikers[gebruiker]['emoji'] = emoji
    elif emoji in premium_emojis:
        # Premium emoji, check of unlocked
        unlocked_emojis = gebruikers[gebruiker].get('unlocked_emojis', [])
        if emoji in unlocked_emojis:
            gebruikers[gebruiker]['emoji'] = emoji
        else:
            return redirect(url_for('profiel_pagina', gebruiker=gebruiker, unlock_error='Deze emoji is nog niet unlocked!'))

    return redirect(url_for('profiel_pagina', gebruiker=gebruiker))

@app.route('/profiel/unlock', methods=['POST'])
def profiel_unlock():
    # VULNERABILITY: IDOR - Takes gebruiker from form without verification
    gebruiker = request.form.get('gebruiker', '')
    code = request.form.get('code', '').strip().upper()

    if not gebruiker or gebruiker not in gebruikers:
        return "Ongeldige gebruiker."

    # Check of code geldig is
    unlocked_emoji = None
    for emoji, valid_code in premium_emojis.items():
        if code == valid_code:
            unlocked_emoji = emoji
            break

    if unlocked_emoji:
        # Check of al unlocked
        unlocked_emojis = gebruikers[gebruiker].get('unlocked_emojis', [])
        if unlocked_emoji in unlocked_emojis:
            return redirect(url_for('profiel_pagina', gebruiker=gebruiker, unlock_error='Je hebt deze emoji al unlocked!'))

        # Unlock de emoji
        unlocked_emojis.append(unlocked_emoji)
        gebruikers[gebruiker]['unlocked_emojis'] = unlocked_emojis

        return redirect(url_for('profiel_pagina', gebruiker=gebruiker, unlock_success=f'Premium emoji {unlocked_emoji} unlocked!'))
    else:
        return redirect(url_for('profiel_pagina', gebruiker=gebruiker, unlock_error='Ongeldige giftcard code!'))

admin_login_html = base_css + '''
<div class="container">
  <div class="login-container">
    <div style="text-align: center; font-size: 3rem; margin-bottom: 1rem;">🔐</div>
    <h2>Admin Login</h2>
    {% if error %}
    <div class="error">{{ error }}</div>
    {% endif %}
    <form action="/admin" method="post">
      <div class="form-group">
        <label>Admin Wachtwoord</label>
        <input type="password" name="admin_password" required placeholder="Voer admin wachtwoord in">
      </div>
      <input type="submit" value="Inloggen als Admin">
    </form>
    <!-- Admin password: admin123 -->
  </div>
</div>
'''

admin_dashboard_html = base_css + '''
<div class="container">
  <div class="header">
    <h2>🔐 Admin Dashboard</h2>
    <div class="header-icons">
      <button onclick="toggleWachtwoorden()" style="background: rgba(255,255,255,0.2); color: white; border: none; padding: 0.5rem 1rem; border-radius: 0.5rem; cursor: pointer; font-family: inherit; font-size: 0.9rem; font-weight: 600;">
        👁️ <span id="toggleText">Toon wachtwoorden</span>
      </button>
    </div>
  </div>

  <div class="section">
    <div class="section-title">Gebruikersbeheer</div>
    <p style="margin-bottom: 1rem; color: #666;">Alle geregistreerde gebruikers en hun statistieken</p>
    <table>
      <thead>
        <tr>
          <th>👤 Gebruiker</th>
          <th>😀 Avatar</th>
          <th>🤖 Bot</th>
          <th>🔑 Wachtwoord</th>
          <th>🎁 Premium</th>
          <th>📥 Ontvangen</th>
          <th>📤 Verzonden</th>
          <th>⚙️ Acties</th>
        </tr>
      </thead>
      <tbody>
        {% for g in gebruikers_stats %}
        <tr>
          <td><strong>{{ g.naam }}</strong></td>
          <td style="font-size: 1.5rem;">{{ g.emoji }}</td>
          <td>{{ '✅' if g.is_bot else '❌' }}</td>
          <td>
            <code class="wachtwoord-veld" data-wachtwoord="{{ g.wachtwoord }}" style="background: #f0f0f0; padding: 0.25rem 0.5rem; border-radius: 0.25rem; cursor: pointer;">••••••••</code>
          </td>
          <td><span style="font-size: 1.2rem;">{{ ' '.join(g.unlocked_emojis) if g.unlocked_emojis else '-' }}</span></td>
          <td>{{ g.ontvangen }}</td>
          <td>{{ g.verzonden }}</td>
          <td>
            <a href="/admin/verwijder?naam={{ g.naam }}" onclick="return confirm('Weet je het zeker?')">🗑️ Verwijder</a>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>

<script>
  let wachtwoordenZichtbaar = false;

  function toggleWachtwoorden() {
    wachtwoordenZichtbaar = !wachtwoordenZichtbaar;
    const wachtwoordVelden = document.querySelectorAll('.wachtwoord-veld');
    const toggleText = document.getElementById('toggleText');

    wachtwoordVelden.forEach(veld => {
      const wachtwoord = veld.getAttribute('data-wachtwoord');
      if (wachtwoordenZichtbaar) {
        veld.textContent = wachtwoord;
        toggleText.textContent = 'Verberg wachtwoorden';
      } else {
        veld.textContent = '••••••••';
        toggleText.textContent = 'Toon wachtwoorden';
      }
    });
  }
</script>
'''

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        # VULNERABILITY: Hardcoded admin password check
        admin_password = request.form.get('admin_password', '')
        if admin_password == 'admin123':
            # Toon dashboard
            gebruikers_stats = []
            for user in gebruikers.keys():
                ontvangen_aantal = sum(1 for b in berichten if b['ontvanger'] == user)
                verzonden_aantal = sum(1 for b in berichten if b['verzender'] == user)
                gebruikers_stats.append({
                    'naam': user,
                    'emoji': gebruikers[user]['emoji'],
                    'is_bot': gebruikers[user].get('is_bot', False),
                    'unlocked_emojis': gebruikers[user].get('unlocked_emojis', []),
                    'ontvangen': ontvangen_aantal,
                    'verzonden': verzonden_aantal,
                    'wachtwoord': gebruikers[user]['password']  # VULNERABILITY: Passwords visible!
                })
            return render_template_string(admin_dashboard_html, gebruikers_stats=gebruikers_stats)
        else:
            return render_template_string(admin_login_html, error="Verkeerd admin wachtwoord!")
    else:
        # Toon login formulier
        return render_template_string(admin_login_html)

@app.route('/admin/verwijder')
def admin_verwijder():
    # VULNERABILITY: IDOR - No authentication check at all!
    naam = request.args.get('naam')
    if naam in gebruikers:
        del gebruikers[naam]
        global berichten
        berichten = [b for b in berichten if b['verzender'] != naam and b['ontvanger'] != naam]
    # Redirect terug naar admin login (niet dashboard want geen auth check)
    return redirect(url_for('admin'))

# Initialiseer bots bij het starten (ook voor Azure)
initialiseer_bots()

if __name__ == '__main__':
    import os
    # Azure App Service sets PORT environment variable
    port = int(os.environ.get('PORT', 8000))
    # debug=False for production, host='0.0.0.0' to listen on all interfaces
    app.run(host='0.0.0.0', port=port, debug=False)
