#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QGridLayout,
    QPushButton, QLineEdit, QTextEdit, QLabel, QMessageBox
)
from PyQt6.QtCore import QObject, QThread, pyqtSignal, Qt

class Worker(QObject):
    finished = pyqtSignal(bool, str)
    def run_task(self, cmd_list):

        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            result = subprocess.run(
                cmd_list, 
                capture_output=True, 
                text=True, 
                check=True, 
                encoding='utf-8',
                startupinfo=startupinfo
            )
            self.finished.emit(True, result.stdout)

        except subprocess.CalledProcessError as e:
            error_output = e.stderr if e.stderr else e.stdout
            self.finished.emit(False, f"Error al ejecutar: {' '.join(cmd_list)}\n{error_output.strip()}")
            
        except FileNotFoundError:
            self.finished.emit(False, f"Error: Comando '{cmd_list[0]}' no encontrado.\n¿Está 'winget' instalado y en el PATH del sistema?")
            
        except Exception as e:
            self.finished.emit(False, f"Error inesperado: {str(e)}")


class WingetManager(QWidget):
    task_requested = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.thread = QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.thread) 
        self.initUI()
        self.connect_signals()
        self.thread.start()

    def initUI(self):
        main_layout = QVBoxLayout()
        input_label = QLabel("Paquetes (separados por espacio) o término de búsqueda:")
        self.package_input = QLineEdit()
        self.package_input.setPlaceholderText("Ej: 'powertoys' o 'microsoft visualstudio'")
        main_layout.addWidget(input_label)
        main_layout.addWidget(self.package_input)
        button_layout = QGridLayout()
        self.install_button = QPushButton("Instalar")
        self.uninstall_button = QPushButton("Desinstalar")
        self.search_button = QPushButton("Buscar")
        self.list_button = QPushButton("Listar Instalados")
        self.upgrade_button = QPushButton("Actualizar Todo")
        button_layout.addWidget(self.install_button, 0, 0)
        button_layout.addWidget(self.uninstall_button, 0, 1)
        button_layout.addWidget(self.search_button, 0, 2)
        button_layout.addWidget(self.list_button, 1, 0)
        button_layout.addWidget(self.upgrade_button, 1, 1, 1, 2)
        main_layout.addLayout(button_layout)
        output_label = QLabel("Salida del comando:")
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setFontFamily("Courier")
        main_layout.addWidget(output_label)
        main_layout.addWidget(self.output_area)
        self.setLayout(main_layout)
        self.setWindowTitle("Gestor de paquetes.")
        self.setGeometry(300, 300, 700, 500)

    def connect_signals(self):
        self.install_button.clicked.connect(self.on_install)
        self.uninstall_button.clicked.connect(self.on_uninstall)
        self.search_button.clicked.connect(self.on_search)
        self.list_button.clicked.connect(self.on_list)
        self.upgrade_button.clicked.connect(self.on_upgrade)
        self.task_requested.connect(self.worker.run_task)

        self.worker.finished.connect(self.on_task_finished)

    
    def on_install(self):
        packages = self.package_input.text().split()
        if not packages:
            self.show_error("Entrada vacía", "Por favor, ingresa uno o más IDs de paquete para instalar.")
            return

        common_flags = ["--accept-package-agreements", "--accept-source-agreements"]
        cmd = ["winget", "install"] + packages + common_flags
        
        self.output_area.setText(f"Iniciando instalación de: {' '.join(packages)}...")
        self.task_requested.emit(cmd)

    def on_uninstall(self):
        packages = self.package_input.text().split()
        if not packages:
            self.show_error("Entrada vacía", "Por favor, ingresa uno o más IDs de paquete para desinstalar.")
            return

        common_flags = ["--accept-source-agreements"]
        cmd = ["winget", "uninstall"] + packages + common_flags

        self.output_area.setText(f"Iniciando desinstalación de: {' '.join(packages)}...")
        self.task_requested.emit(cmd)

    def on_search(self):
        pattern = self.package_input.text()
        if not pattern:
            self.show_error("Entrada vacía", "Por favor, ingresa un término de búsqueda.")
            return
            
        cmd = ["winget", "search", pattern]
        self.output_area.setText(f"Buscando: '{pattern}'...")
        self.task_requested.emit(cmd)
        
    def on_list(self):
        cmd = ["winget", "list"]
        self.output_area.setText("Obteniendo lista de paquetes instalados...")
        self.task_requested.emit(cmd)
        
    def on_upgrade(self):
        common_flags = ["--all", "--accept-package-agreements", "--accept-source-agreements"]
        cmd = ["winget", "upgrade"] + common_flags
        self.output_area.setText("Buscando e instalando actualizaciones del sistema...")
        self.task_requested.emit(cmd)

    def on_task_finished(self, success, output):
        """ Se llama cuando el hilo de trabajo ha terminado. """
        if success:
            self.output_area.setText(output)
        else:
            self.output_area.setText(f"OPERACIÓN FALLIDA:\n\n{output}")
            self.show_error("Error de Winget", output)

    def show_error(self, title, message):

        QMessageBox.critical(self, title, message)

    def closeEvent(self, event):

        self.output_area.setText("Cerrando... esperando al hilo de trabajo.")
        self.thread.quit()
        self.thread.wait()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WingetManager()
    window.show()
    sys.exit(app.exec())