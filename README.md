# DatosGT Social Analytics

Analisis cruzado de Instagram y TikTok para optimizar guiones y formato de video.

## 1. Instalar dependencias

```
pip install -r requirements.txt
```

## 2. Obtener credenciales (esto lo haces tu, con tu login)

### Instagram (Meta Graph API)

1. Tu cuenta de Instagram debe ser Business o Creator, vinculada a una Pagina de Facebook.
2. Entra a https://developers.facebook.com/apps y crea una app tipo "Business".
3. Agrega el producto **Instagram Graph API**.
4. En Graph API Explorer, genera un access token de usuario con los permisos:
   `instagram_basic`, `instagram_manage_insights`, `pages_show_list`, `pages_read_engagement`.
5. Consigue tu `IG_BUSINESS_ACCOUNT_ID` con:
   `GET /me/accounts` -> `GET /{page-id}?fields=instagram_business_account`

### TikTok (TikTok for Developers)

1. Entra a https://developers.tiktok.com/apps y registra una app (login con tu cuenta de TikTok).
2. En la app, agrega el producto **Login Kit**.
3. En la configuracion de Login Kit, agrega esta Redirect URI exactamente:
   `http://localhost:8921/callback`
4. En "Basic Information" copia el `Client key` y `Client secret` a tu `config\.env`
   (`TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET`).
5. En "Scopes", habilita `user.info.basic` y `video.list`.
6. Corre el helper de autorizacion (abre tu navegador, tu apruebas el acceso, y guarda el token solo):

```
cd scripts
python tiktok_oauth_helper.py
```

Esto llena automaticamente `TIKTOK_ACCESS_TOKEN` y `TIKTOK_OPEN_ID` en tu `.env`.
Nota: este token vence pronto (revisa `expires_in` que imprime el script); si el loop diario
empieza a fallar por token vencido, vuelve a correr este helper.

## 3. Configurar

```
copy config\.env.example config\.env
```

Pega los valores obtenidos en el paso 2 dentro de `config\.env`.

## 4. Correr manualmente

```
cd scripts
python run_daily.py
```

Esto genera:
- `data/instagram_posts.json`, `data/tiktok_posts.json` — datos crudos
- `reports/report_YYYY-MM-DD.md` — analisis cruzado con recomendaciones de guion

## 5. Automatizar (loop diario)

Una vez que corra bien manualmente, se programa como tarea diaria automatica.
