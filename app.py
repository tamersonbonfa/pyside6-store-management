import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from database.db import init_db
from services.auth_service import ensure_admin_user
from services.config_service import get_config
from ui.themes import qss_dark, qss_light
from ui.login_dialog import LoginDialog


def main():

    app = QApplication(sys.argv)
    
    #INICIAR BANCO DE DADOS
    try:
        init_db()
    except Exception:
        QMessageBox.critical(
            "Falha ao conectar no banco de dados."
        )
        return 1
    
    theme = get_config("theme", "dark").lower()
    if theme == "light":
        app.setStyleSheet(qss_light())
    else:
        app.setStyleSheet(qss_dark())

    w = LoginDialog()
    w.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
