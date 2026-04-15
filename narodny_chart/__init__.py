try:
    import pymysql

    pymysql.install_as_MySQLdb()
except Exception:
    # Fallback keeps the project importable even before dependencies are installed.
    pass
