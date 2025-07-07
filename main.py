from flask import Flask, request, redirect, url_for, render_template_string
import urllib.parse
import re

app = Flask(__name__)
gebruikers = []
berichten = []

base_css = '''
<style>
  body {
    font-family: system-ui, sans-serif;
    background-color: #f4f4f8;
    margin: 0;
    padding: 2rem;
    color: #333;
  }
  h2, h3 {
    color: #444;
  }
  form {
    background: white;
    padding: 1rem;
    border-radius: 0.5rem;
    max-width: 400px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.1);
  }
  input[type="text"], select, textarea, input[type="submit"] {
    padding: 0.5rem;
    margin-top: 0.5rem;
    width: 100%;
    box-sizing: border-box;
    border: 1px solid #ccc;
    border-radius: 0.4rem;
    font-family: system-ui, sans-serif;
  }
  textarea {
    resize: vertical;
  }
  input[type="submit"] {
    background: #4caf50;
    color: white;
    border: none;
    cursor: pointer;
  }
  input[type="submit"]:hover {
    background: #45a049;
  }
  ul {
    list-style: none;
    padding: 0;
  }
  li {
    background: white;
    padding: 0.75rem;
    margin-bottom: 0.5rem;
    border-radius: 0.4rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    white-space: pre-wrap;
  }
  a {
    display: inline-block;
    margin-top: 1rem;
    text-decoration: none;
    color: #2196f3;
  }
  a.verwijder {
    color: red;
    margin-left: 10px;
  }
  table {
    border-collapse: collapse;
    width: 100%;
    max-width: 600px;
    background: white;
    border-radius: 0.5rem;
    box-shadow: 0 2px 6px rgba(0,0,0,0.1);
  }
  th, td {
    border: 1px solid #ccc;
    padding: 0.5rem 1rem;
    text-align: left;
  }
  th {
    background-color: #eee;
  }
</style>
'''

verboden_woorden = ["fuck", "poep", "schijt", "stom", "eikel", "klootzak", "stommerd"]

def filter_verboden_woorden(tekst):
    def vervang(match):
        return '*' * len(match.group())
    patroon = re.compile('|'.join(re.escape(w) for w in verboden_woorden), re.IGNORECASE)
    return patroon.sub(vervang, tekst)

registreer_html = base_css + '''
<h2>Registreer</h2>
<form action="/registreer" method="post">
  <label>Gebruikersnaam:</label>
  <input type="text" name="naam" required>
  <input type="submit" value="Registreer">
</form>
'''

berichten_html = base_css + '''
<a href="/gebruikers?gebruiker={{ gebruiker }}">Alle gebruikers</a>
<h2>Berichten voor {{ gebruiker }}</h2>

<h3>Ontvangen berichten</h3>
<ul>
  {% for b in ontvangen %}
    <li>
      <strong>Van:</strong> {{ b['verzender'] }}<br>
      {{ b['inhoud'] | e }}<br>
      <a href="/nieuwbericht?verzender={{ gebruiker }}&ontvanger={{ b['verzender'] }}&quote_verzender={{ b['verzender'] | url_encode }}&quote_inhoud={{ b['inhoud'] | url_encode }}">Antwoord</a>
      <a href="/verwijder_bericht?gebruiker={{ gebruiker }}&index={{ loop.index0 }}" class="verwijder">Verwijder</a>
    </li>
  {% else %}
    <li>Geen ontvangen berichten.</li>
  {% endfor %}
</ul>

<h3>Verstuurde berichten</h3>
<ul>
  {% for b in verzonden %}
    <li>
      <strong>Aan:</strong> {{ b['ontvanger'] }}<br>
      {{ b['inhoud'] | e }}
    </li>
  {% else %}
    <li>Geen verstuurde berichten.</li>
  {% endfor %}
</ul>

<a href="/nieuwbericht?verzender={{ gebruiker }}">Nieuw bericht schrijven</a>
'''

nieuwbericht_html = base_css + '''
<h2>Nieuw bericht van {{ verzender }}</h2>
<form action="/nieuwbericht" method="post">
  <input type="hidden" name="verzender" value="{{ verzender }}">
  <label>Ontvanger:</label>
  <select name="ontvanger" required>
    {% for user in gebruikers %}
      {% if user != verzender %}
        <option value="{{ user }}" {% if ontvanger == user %}selected{% endif %}>{{ user }}</option>
      {% endif %}
    {% endfor %}
  </select>
  <label>Bericht:</label>
  <textarea name="inhoud" required rows="6">{{ voorafgaande_tekst }}</textarea>
  <input type="submit" value="Verstuur">
</form>
'''

gebruikers_html = base_css + '''
<h2>Alle gebruikers</h2>
<ul>
  {% for user in gebruikers %}
    <li><a href="/nieuwbericht?verzender={{ huidige_gebruiker }}&ontvanger={{ user }}">{{ user }}</a></li>
  {% endfor %}
</ul>
<a href="/berichten?gebruiker={{ huidige_gebruiker }}">Terug naar berichten</a>
'''

@app.template_filter('url_encode')
def url_encode_filter(s):
    return urllib.parse.quote_plus(s)

@app.route('/')
def home():
    return redirect(url_for('registreer_get'))

@app.route('/registreer', methods=['GET'])
def registreer_get():
    return render_template_string(registreer_html)

@app.route('/registreer', methods=['POST'])
def registreer_post():
    naam = request.form.get('naam', '').strip()
    if not naam or naam in gebruikers:
        return "Gebruikersnaam ongeldig of al in gebruik."
    if any(re.search(r'\b' + re.escape(w) + r'\b', naam, re.IGNORECASE) for w in verboden_woorden):
        return "Deze gebruikersnaam is niet toegestaan vanwege ongepaste woorden."
    gebruikers.append(naam)
    return redirect(f"/berichten?gebruiker={naam}")

@app.route('/berichten')
def berichten_pagina():
    gebruiker = request.args.get('gebruiker')
    if gebruiker in gebruikers:
        ontvangen = [b for b in berichten if b['ontvanger'] == gebruiker]
        verzonden = [b for b in berichten if b['verzender'] == gebruiker]
        return render_template_string(berichten_html, gebruiker=gebruiker, ontvangen=ontvangen, verzonden=verzonden)
    return "Ongeldige gebruiker."

@app.route('/nieuwbericht', methods=['GET', 'POST'])
def nieuw_bericht():
    if request.method == 'GET':
        verzender = request.args.get('verzender')
        ontvanger = request.args.get('ontvanger', '')
        quote_verzender = request.args.get('quote_verzender', '')
        quote_inhoud = request.args.get('quote_inhoud', '')

        if verzender in gebruikers:
            voorafgaande_tekst = ''
            if quote_verzender and quote_inhoud:
                voorafgaande_tekst = f"[quote van {quote_verzender}]\n{quote_inhoud}\n[/quote]\n\n"
            return render_template_string(
                nieuwbericht_html,
                verzender=verzender,
                ontvanger=ontvanger,
                gebruikers=gebruikers,
                voorafgaande_tekst=voorafgaande_tekst
            )
        return "Ongeldige verzender."
    else:
        verzender = request.form.get('verzender')
        ontvanger = request.form.get('ontvanger')
        inhoud = request.form.get('inhoud')
        if verzender in gebruikers and ontvanger in gebruikers:
            inhoud = filter_verboden_woorden(inhoud)
            berichten.append({'verzender': verzender, 'ontvanger': ontvanger, 'inhoud': inhoud})
            return redirect(f"/berichten?gebruiker={verzender}")
        return "Ongeldige verzender of ontvanger."

@app.route('/verwijder_bericht')
def verwijder_bericht():
    gebruiker = request.args.get('gebruiker')
    try:
        index = int(request.args.get('index'))
    except (TypeError, ValueError):
        return "Ongeldige index."

    if gebruiker in gebruikers:
        ontvangen = [b for b in berichten if b['ontvanger'] == gebruiker]
        if 0 <= index < len(ontvangen):
            bericht_to_delete = ontvangen[index]
            berichten.remove(bericht_to_delete)
            return redirect(f"/berichten?gebruiker={gebruiker}")
        else:
            return "Bericht niet gevonden."
    return "Ongeldige gebruiker."

@app.route('/gebruikers')
def gebruikers_pagina():
    huidige_gebruiker = request.args.get('gebruiker', '')
    if huidige_gebruiker not in gebruikers:
        return "Ongeldige gebruiker."
    return render_template_string(gebruikers_html, gebruikers=gebruikers, huidige_gebruiker=huidige_gebruiker)

@app.route('/admin')
def admin():
    gebruikers_stats = []
    for user in gebruikers:
        ontvangen_aantal = sum(1 for b in berichten if b['ontvanger'] == user)
        verzonden_aantal = sum(1 for b in berichten if b['verzender'] == user)
        gebruikers_stats.append({
            'naam': user,
            'ontvangen': ontvangen_aantal,
            'verzonden': verzonden_aantal
        })
    admin_html = base_css + '''
    <h2>Admin pagina</h2>
    <table>
      <tr><th>Gebruiker</th><th>Ontvangen berichten</th><th>Verzonden berichten</th><th>Acties</th></tr>
      {% for g in gebruikers_stats %}
      <tr>
        <td>{{ g.naam }}</td>
        <td>{{ g.ontvangen }}</td>
        <td>{{ g.verzonden }}</td>
        <td>
          <a href="/admin/verwijder?naam={{ g.naam }}" onclick="return confirm('Weet je het zeker?')">Verwijder</a>
        </td>
      </tr>
      {% endfor %}
    </table>
    '''
    return render_template_string(admin_html, gebruikers_stats=gebruikers_stats)

@app.route('/admin/verwijder')
def admin_verwijder():
    naam = request.args.get('naam')
    if naam in gebruikers:
        gebruikers.remove(naam)
        global berichten
        berichten = [b for b in berichten if b['verzender'] != naam and b['ontvanger'] != naam]
        return redirect('/admin')
    return "Gebruiker niet gevonden."

if __name__ == '__main__':
    app.run(debug=True)
