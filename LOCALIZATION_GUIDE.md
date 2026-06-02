# Localization Guide

This app now supports multiple languages! All code and infrastructure are in English, but the UI text is translatable.

## ✅ What's Already Done

1. **Login page** - Fully translated (NL/EN)
2. **Language switcher** - Top right corner (🇳🇱 NL / 🇬🇧 EN)
3. **Translation system** - `translations.py` with all UI text
4. **Session-based** - Language preference is remembered

## 🎯 How It Works

### Code Structure (English)
```python
# Variable names in English
gebruikers = {}  # users
berichten = []   # messages

# Comments in English
def get_language():
    """Get current language from session"""
    return session.get('language', 'nl')
```

### UI Text (Translatable)
```python
# In translations.py
TRANSLATIONS = {
    'nl': {
        'login': 'Inloggen',
        'username': 'Gebruikersnaam',
    },
    'en': {
        'login': 'Login',
        'username': 'Username',
    }
}
```

## 📝 How to Update Other Pages

### Step 1: Update the HTML Template

**Before:**
```python
some_html = base_css + '''
<h2>Inloggen</h2>
<label>Gebruikersnaam</label>
<input type="submit" value="Inloggen">
'''
```

**After:**
```python
some_html = base_css + '''
<div class="language-switcher">
  <a href="/language/nl" class="lang-btn {{ 'active' if current_lang == 'nl' else '' }}">🇳🇱 NL</a>
  <a href="/language/en" class="lang-btn {{ 'active' if current_lang == 'en' else '' }}">🇬🇧 EN</a>
</div>

<h2>{{ t.login }}</h2>
<label>{{ t.username }}</label>
<input type="submit" value="{{ t.login }}">
'''
```

### Step 2: Update the Route Function

**Before:**
```python
@app.route('/some-page')
def some_page():
    return render_template_string(some_html, data=data)
```

**After:**
```python
@app.route('/some-page')
def some_page():
    lang = get_language()
    return render_template_string(some_html, data=data, t=get_all(lang), current_lang=lang)
```

### Step 3: Add Error Messages

**Before:**
```python
return render_template_string(some_html, error="Fout bericht")
```

**After:**
```python
return render_template_string(some_html, error=t('error_key'), t=get_all(lang), current_lang=lang)
```

## 🌍 Adding New Languages

To add a new language (e.g., German):

1. Open `translations.py`
2. Add a new section:

```python
TRANSLATIONS = {
    'nl': { ... },
    'en': { ... },
    'de': {  # New!
        'login': 'Anmelden',
        'username': 'Benutzername',
        ...
    }
}
```

3. Update language switcher in templates:

```html
<div class="language-switcher">
  <a href="/language/nl" class="lang-btn">🇳🇱 NL</a>
  <a href="/language/en" class="lang-btn">🇬🇧 EN</a>
  <a href="/language/de" class="lang-btn">🇩🇪 DE</a>
</div>
```

4. Update `/language/<lang>` route:

```python
@app.route('/language/<lang>')
def set_language(lang):
    if lang in ['nl', 'en', 'de']:  # Add 'de'
        session['language'] = lang
    return redirect(request.referrer or url_for('home'))
```

## 📋 Pages to Update

Here's a checklist of pages that still need translation:

- [ ] Register page (`registreer_html`)
- [ ] Messages page (`berichten_html`)
- [ ] New message page (`nieuwbericht_html`)
- [ ] Users page (`gebruikers_html`)
- [ ] Profile page (`profiel_html`)
- [ ] Admin login (`admin_login_html`)
- [ ] Admin dashboard (`admin_dashboard_html`)

## 💡 Tips

1. **Always pass translations**: Every render must include `t=get_all(lang), current_lang=lang`
2. **Use translation keys**: Replace Dutch text with `{{ t.translation_key }}`
3. **Language switcher**: Add to every page for consistency
4. **Test both languages**: Switch languages and test all pages
5. **Bot messages**: Currently in Dutch/English mix - keep them fun and localized!

## 🔍 Example: Full Page Update

Here's the complete pattern for the register page:

```python
# 1. Update HTML template
registreer_html = base_css + '''
<div class="language-switcher">
  <a href="/language/nl" class="lang-btn {{ 'active' if current_lang == 'nl' else '' }}">🇳🇱 NL</a>
  <a href="/language/en" class="lang-btn {{ 'active' if current_lang == 'en' else '' }}">🇬🇧 EN</a>
</div>

<div class="container">
  <div class="register-container">
    <div class="app-logo"></div>
    <h2>{{ t.create_account }}</h2>
    {% if error %}
    <div class="error">{{ error }}</div>
    {% endif %}
    <form action="/registreer" method="post">
      <div class="form-group">
        <label>{{ t.choose_username }}</label>
        <input type="text" name="naam" required placeholder="{{ t.username }}">
      </div>
      <div class="form-group">
        <label>{{ t.choose_password }}</label>
        <input type="password" name="wachtwoord" required placeholder="{{ t.password }}">
      </div>
      <input type="submit" value="{{ t.register }}">
    </form>
    <p class="link-text">{{ t.have_account }} <a href="/login">{{ t.login }}</a></p>
  </div>
</div>
'''

# 2. Update GET route
@app.route('/registreer', methods=['GET'])
def registreer_get():
    lang = get_language()
    return render_template_string(registreer_html, t=get_all(lang), current_lang=lang)

# 3. Update POST route
@app.route('/registreer', methods=['POST'])
def registreer_post():
    lang = get_language()
    naam = request.form.get('naam', '').strip()
    wachtwoord = request.form.get('wachtwoord', '')

    if not naam:
        return render_template_string(registreer_html, error=t('username_empty'), t=get_all(lang), current_lang=lang)

    if naam in gebruikers:
        return render_template_string(registreer_html, error=t('username_taken'), t=get_all(lang), current_lang=lang)

    # ... rest of logic
    session['ingelogd_als'] = naam
    return redirect(url_for('berichten_pagina', gebruiker=naam))
```

## 🚀 Quick Start

1. **Test current setup**: Login page is already translated - try it!
2. **Pick a page**: Start with register or messages
3. **Update HTML**: Replace Dutch text with `{{ t.key }}`
4. **Update route**: Add `t=get_all(lang), current_lang=lang`
5. **Test**: Switch languages and verify it works

## 📦 What's in translations.py

All UI text is organized by feature:
- General (app_name, back, logout, etc.)
- Login page
- Register page
- Messages page
- Profile page
- Admin page
- Error messages

Just use the keys in your templates: `{{ t.login }}`, `{{ t.username }}`, etc.
