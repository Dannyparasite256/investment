"""Quick smoke test against local dev server."""
import re
import urllib.error
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar

BASE = 'http://127.0.0.1:8080'


def main():
    for path in ['/', '/accounts/login/', '/accounts/register/', '/investments/', '/api/v1/plans/', '/api/docs/']:
        try:
            r = urllib.request.urlopen(BASE + path)
            print(path, r.status, len(r.read()))
        except Exception as e:
            print(path, 'ERR', e)

    cj = CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    login_page = opener.open(BASE + '/accounts/login/').read().decode()
    m = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', login_page)
    if not m:
        print('CSRF token not found')
        return
    csrf = m.group(1)
    data = urllib.parse.urlencode({
        'username': 'admin@cryptoinvest.local',
        'password': 'AdminPass123!',
        'remember_me': 'on',
        'csrfmiddlewaretoken': csrf,
    }).encode()
    req = urllib.request.Request(
        BASE + '/accounts/login/',
        data=data,
        headers={
            'Referer': BASE + '/accounts/login/',
            'Content-Type': 'application/x-www-form-urlencoded',
        },
    )
    try:
        resp = opener.open(req)
        print('LOGIN', resp.status, resp.geturl())
    except urllib.error.HTTPError as e:
        print('LOGIN ERR', e.code, e.read()[:400])
        return

    dash = opener.open(BASE + '/dashboard/')
    body = dash.read()
    print('DASH', dash.status, len(body))
    print('OK' if b'Available Balance' in body or b'Dashboard' in body else 'DASH content unexpected')


if __name__ == '__main__':
    main()
