import sys

from PySide6.QtWidgets import QApplication, QMessageBox, QDialog

from database.db import init_db
from services.usuario_service import existe_usuario_admin
from services.config_service import get_config
from ui.themes import qss_dark, qss_light
from ui.login_dialog import LoginDialog
from ui.admin_setup_dialog import AdminSetupDialog


def main():

    app = QApplication(sys.argv)
    
    #INICIAR BANCO DE DADOS
    try:
        init_db()
    except Exception:
        QMessageBox.critical(
            None,
            "Erro",
            "Falha ao conectar no banco de dados."
        )
        return 1
    
    theme = get_config("theme", "dark").lower()
    if theme == "light":
        app.setStyleSheet(qss_light())
    else:
        app.setStyleSheet(qss_dark())
    
    if not existe_usuario_admin():
        
        setup = AdminSetupDialog()
        
        if setup.exec() != QDialog.Accepted:
            return 0

    login = LoginDialog()
    login.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
