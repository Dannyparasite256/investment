# Deploy CryptoInvest on PythonAnywhere

Repo: https://github.com/Dannyparasite256/investment

Replace `investment256` with **your** PythonAnywhere username if different.

---

## 1. Create account

1. Sign up / log in: https://www.pythonanywhere.com  
2. Note your username (example: `investment256`)  
3. Your site will be: `https://YOUR_USERNAME.pythonanywhere.com`

---

## 2. Open a Bash console

**Dashboard → Consoles → Bash**

```bash
cd ~
git clone https://github.com/Dannyparasite256/investment.git
cd investment
```

If the folder already exists:

```bash
cd ~/investment
git pull origin main
```

---

## 3. Virtualenv + packages

```bash
cd ~/investment
python3.12 -m venv venv
# If 3.12 missing, try: python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 4. Create `.env`

```bash
cd ~/investment
cp .env.pythonanywhere.example .env
nano .env
```

Edit at least:

- `SECRET_KEY` — long random string  
- `ALLOWED_HOSTS` — `YOUR_USERNAME.pythonanywhere.com`  
- `CSRF_TRUSTED_ORIGINS` — `https://YOUR_USERNAME.pythonanywhere.com`  
- `SITE_URL` — same HTTPS URL  

Generate a secret:

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

Save in nano: `Ctrl+O`, Enter, `Ctrl+X`.

---

## 5. Database + static + admin

```bash
cd ~/investment
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
python manage.py seed_platform
```

---

## 6. Web app setup

1. Go to **Web** tab  
2. **Add a new web app**  
3. Choose **Manual configuration** (not the Django wizard)  
4. Pick the same Python version as your venv (3.12 or 3.11)  
5. Set:

| Field | Value |
|--------|--------|
| Source code | `/home/YOUR_USERNAME/investment` |
| Working directory | `/home/YOUR_USERNAME/investment` |
| Virtualenv | `/home/YOUR_USERNAME/investment/venv` |

---

## 7. WSGI file

On the Web tab, open the **WSGI configuration file** link.  
Delete the default content and paste:

```python
import os
import sys

project_home = '/home/YOUR_USERNAME/investment'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.chdir(project_home)
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

Save.

---

## 8. Static & media mappings

On the **Web** tab → **Static files**:

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/YOUR_USERNAME/investment/staticfiles` |
| `/media/` | `/home/YOUR_USERNAME/investment/media` |

Create media folder if needed:

```bash
mkdir -p ~/investment/media
```

---

## 9. Reload

Click the green **Reload** button on the Web tab.

Visit:

`https://YOUR_USERNAME.pythonanywhere.com`

---

## 10. First login

- Staff seed (if seed ran): check seed output / create superuser email  
- Or use the superuser you created in step 5  
- Django admin: `/admin/`  
- Staff panel: `/staff/`

---

## Update code later

```bash
cd ~/investment
source venv/bin/activate
git pull origin main
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

Then **Reload** the web app.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| DisallowedHost | Fix `ALLOWED_HOSTS` in `.env` to exact hostname |
| CSRF verification failed | Fix `CSRF_TRUSTED_ORIGINS` with `https://...` |
| No CSS | Run `collectstatic` + static file mapping |
| 500 error | Web tab → **Error log** |
| Module not found | Activate correct virtualenv path on Web tab |
| Upload images fail | Map `/media/` and `mkdir media` |

View logs:

```bash
# Also in Web → Log files
tail -n 50 /var/log/YOUR_USERNAME.pythonanywhere.com.error.log
```
