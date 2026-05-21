from sqlalchemy.engine import make_url
url = make_url('postgresql+asyncpg://user:pass@dpg-cabc123-a/db')
sync_url = url.set(drivername='postgresql')
print('driver:', sync_url.drivername)
print('host:', sync_url.host)
print('render_as_string:', sync_url.render_as_string(hide_password=False))
