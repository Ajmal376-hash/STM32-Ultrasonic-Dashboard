import sys
import serial
from serial.tools import list_ports
import pyqtgraph as pg

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout
)
from PySide6.QtCore import Qt, QTimer, QTime


class Dashboard(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Industrial Ultrasonic Monitoring System")
        self.resize(1600, 900)

        self.setStyleSheet("""
        QMainWindow{
            background-color:#101418;
        }

        QLabel{
            color:white;
            font-family:Segoe UI;
        }
        """)

        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        central.setLayout(layout)

        # ================= HEADER =================
        title = QLabel("SMART ULTRASONIC MONITORING SYSTEM")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
        font-size:30px;
        color:#00E5FF;
        font-weight:bold;
        """)
        layout.addWidget(title)

        # ================= STATUS =================
        self.status = QLabel()
        self.status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status)

        # ================= SENSOR CARDS =================
        cardLayout = QHBoxLayout()
        cardLayout.setSpacing(20)

        self.s1 = self.createCard("SENSOR 1")
        self.s2 = self.createCard("SENSOR 2")
        self.s3 = self.createCard("SENSOR 3")

        cardLayout.addWidget(self.s1)
        cardLayout.addWidget(self.s2)
        cardLayout.addWidget(self.s3)

        layout.addLayout(cardLayout)

        # ================= LIVE GRAPH =================
        self.graph = pg.PlotWidget()
        self.graph.setBackground("#1B232D")
        self.graph.setTitle("Live Distance Graph", color="w", size="14pt")
        self.graph.showGrid(x=True, y=True)
        self.graph.setLabel("left", "Distance (cm)")
        self.graph.setLabel("bottom", "Samples")
        self.graph.setYRange(0, 500)

        layout.addWidget(self.graph)

        self.x = list(range(30))
        self.y1 = [0] * 30

        self.line1 = self.graph.plot(
            self.x,
            self.y1,
            pen=pg.mkPen(color="#00E5FF", width=3)
        )

        # ================= FOOTER =================
        footer = QLabel("STM32 • UART • Industrial Dashboard • Version 1.0")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("""
        color:gray;
        font-size:14px;
        """)

        layout.addStretch()
        layout.addWidget(footer)

        # ================= SERIAL & TIMERS =================
        self.ser = None
        self.connectSerial()

        # Real-time data timer (100ms refresh)
        self.dataTimer = QTimer()
        self.dataTimer.timeout.connect(self.processLiveData)
        self.dataTimer.start(100)

        # Clock timer (1sec refresh)
        self.clockTimer = QTimer()
        self.clockTimer.timeout.connect(self.updateClock)
        self.clockTimer.start(1000)

        self.updateClock()

    def createCard(self, title):
        card = QLabel(f"📡 {title}\n\n0 cm\n\n🟢 SAFE")
        card.setAlignment(Qt.AlignCenter)
        card.setFixedSize(350, 220)

        card.setStyleSheet("""
        QLabel{
            background-color:#1B232D;
            border:2px solid #00E5FF;
            border-radius:18px;
            color:white;
            font-size:24px;
            font-weight:bold;
        }
        """)

        return card

    def connectSerial(self):
        try:
            self.ser = serial.Serial('COM7', 115200, timeout=0.05)
            print("Connected to COM7 successfully!")
            return
        except Exception as e:
            print("Connection error:", e)

    def readPICSimLab(self):
        if self.ser is None or not self.ser.is_open:
            return None

        try:
            if self.ser.in_waiting > 0:
                raw_data = self.ser.readline().decode(errors="ignore").strip()

                # Process line if all 3 sensors are present
                if "S1=" in raw_data and "S2=" in raw_data and "S3=" in raw_data:
                    clean_line = raw_data[raw_data.find("S1="):]
                    
                    # Split string by space
                    parts = clean_line.split()
                    
                    s1 = int(parts[0].split("=")[1])
                    s2 = int(parts[1].split("=")[1])
                    s3 = int(parts[2].split("=")[1])
                    
                    return (s1, s2, s3)
        except Exception as e:
            pass

        return None

    def processLiveData(self):
        data = self.readPICSimLab()

        if data:
            s1, s2, s3 = data
            self.updateSensors(s1, s2, s3)

            # Live Graph Plot Update using Sensor 1
            self.y1.append(s1)
            self.y1.pop(0)
            self.line1.setData(self.x, self.y1)

    def updateSensors(self, s1, s2, s3):
        self.updateCardUI(self.s1, "SENSOR 1", s1)
        self.updateCardUI(self.s2, "SENSOR 2", s2)
        self.updateCardUI(self.s3, "SENSOR 3", s3)

    def updateCardUI(self, card, title, value):
        if value < 50:
            status, color = "🔴 DANGER", "#FF3B30"
        elif value < 150:
            status, color = "🟡 WARNING", "#FFC107"
        else:
            status, color = "🟢 SAFE", "#00C853"

        card.setText(f"📡 {title}\n\n📏 {value} cm\n\n{status}")
        card.setStyleSheet(f"""
        QLabel{{
            background-color:#1B232D;
            border:3px solid {color};
            border-radius:18px;
            color:white;
            font-size:22px;
            font-weight:bold;
            padding:10px;
        }}
        """)

        return card

    def updateClock(self):
        time_str = QTime.currentTime().toString("hh:mm:ss")
        status_str = f"🟢 LIVE CONNECTED ({self.ser.port})" if (self.ser and self.ser.is_open) else "🔴 DISCONNECTED"
        self.status.setText(f"{status_str}     |     {time_str}")
        self.status.setStyleSheet("color:#00FF66; font-size:18px; font-weight:bold;")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Dashboard()
    window.show()
    sys.exit(app.exec())