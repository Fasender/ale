import os, sys
from abc import ABC, abstractmethod
from datetime import datetime
from functools import total_ordering
from PySide6.QtWidgets import (QApplication, QWidget, QGridLayout, QLabel, QLineEdit, QPushButton,
                               QComboBox, QCheckBox, QListWidget, QInputDialog)

FMT = "%d.%m.%Y %H:%M:%S"
REPORT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "report.txt")


def prop(name):  # геттер + сеттер для атрибута
    return property(lambda s: getattr(s, "_" + name), lambda s, v: setattr(s, "_" + name, str(v).strip()))


class Entity(ABC):  # абстрактный класс
    @abstractmethod
    def describe(self): ...


@total_ordering
class Contact(Entity):
    name, phone, group = prop("name"), prop("phone"), prop("group")

    def __init__(self, name, phone, group):
        self.name, self.phone, self.group = name, phone, group

    def describe(self): return f"{self.name}, {self.phone}"
    def __eq__(self, o): return isinstance(o, Contact) and (self.name, self.phone) == (o.name, o.phone)
    def __lt__(self, o): return self.name.lower() < o.name.lower()
    def __hash__(self): return hash((self.name, self.phone))
    def __repr__(self): return f"Contact({self.name!r}, {self.phone!r}, {self.group!r})"
    def __str__(self): return self.describe()


class PairMap(Entity):  # свой аналог словаря (вместо dict)
    def __init__(self): self._pairs = []
    def put(self, key, value): self._pairs = [p for p in self._pairs if p[0] != key] + [(key, value)]
    def get(self, key): return next(v for k, v in self._pairs if k == key)
    def keys(self): return [k for k, _ in self._pairs]
    def describe(self): return ", ".join(f"{k}={v}" for k, v in self._pairs)
    def __eq__(self, o): return isinstance(o, PairMap) and self._pairs == o._pairs
    def __len__(self): return len(self._pairs)
    def __repr__(self): return f"PairMap({self._pairs!r})"
    def __str__(self): return self.describe()


class Report:
    @staticmethod
    def save(login, t_in, t_out, path=REPORT):
        line = "+" + "-" * 14 + "+" + "-" * 21 + "+" + "-" * 21 + "+\n"
        is_new = not os.path.exists(path)
        with open(path, "a", encoding="utf-8") as f:
            if is_new:
                f.write(line + f"| {'login':<12} | {'time_in':<19} | {'time_out':<19} |\n" + line)
            f.write(f"| {login.replace('|', ' ')[:12]:<12} | {t_in:{FMT}} | {t_out:{FMT}} |\n" + line)


class HoverButton(QPushButton):  # переопределённый компонент 1
    def enterEvent(self, e): self.setStyleSheet("background:#bcd"); super().enterEvent(e)
    def leaveEvent(self, e): self.setStyleSheet(""); super().leaveEvent(e)


class FocusEdit(QLineEdit):  # переопределённый компонент 2
    def focusInEvent(self, e): self.setStyleSheet("border:2px solid #27f"); super().focusInEvent(e)
    def focusOutEvent(self, e): self.setStyleSheet(""); super().focusOutEvent(e)


class Title(QLabel):  # переопределённый компонент 3
    def mouseDoubleClickEvent(self, e): self.setText("Контакты"); super().mouseDoubleClickEvent(e)


class App(QWidget):
    def __init__(self, login):
        super().__init__()
        self.login, self.t_in = login, datetime.now()
        self.setWindowTitle(f"Контакты — {login}")
        self.groups = PairMap()
        for k, v in (("work", "Работа"), ("family", "Семья"), ("friends", "Друзья")): self.groups.put(k, v)
        self.contacts = [Contact(*a) for a in (("Анна", "+7 900 111-11-11", "family"), ("Борис", "+7 900 222-22-22", "work"),
                         ("Виктор", "+7 900 333-33-33", "friends"), ("Галина", "+7 900 444-44-44", "work"),
                         ("Дмитрий", "+7 900 555-55-55", "friends"))]
        self.name, self.phone, self.combo = FocusEdit(), FocusEdit(), QComboBox()
        self.combo.addItems(self.groups.keys())
        self.sort, self.list = QCheckBox("Сортировать по имени"), QListWidget()
        add, rm = HoverButton("Добавить"), HoverButton("Удалить выбранный")
        g = QGridLayout(self)
        g.addWidget(Title("Контакты (двойной клик — сброс)"), 0, 0, 1, 2)
        for i, (text, w) in enumerate((("Имя:", self.name), ("Телефон:", self.phone), ("Группа:", self.combo)), 1):
            g.addWidget(QLabel(text), i, 0); g.addWidget(w, i, 1)
        g.addWidget(add, 4, 0); g.addWidget(rm, 4, 1); g.addWidget(self.sort, 5, 0, 1, 2); g.addWidget(self.list, 6, 0, 1, 2)
        add.clicked.connect(self.add); rm.clicked.connect(self.remove); self.sort.toggled.connect(self.refresh)
        self.refresh()

    def visible(self): return sorted(self.contacts) if self.sort.isChecked() else self.contacts

    def refresh(self):
        self.list.clear()
        self.list.addItems([f"{c} [{self.groups.get(c.group)}]" for c in self.visible()])

    def add(self):
        if self.name.text().strip() and self.phone.text().strip():
            self.contacts.append(Contact(self.name.text(), self.phone.text(), self.combo.currentText()))
            self.name.clear(); self.phone.clear(); self.refresh()

    def remove(self):
        if self.list.currentRow() >= 0:
            self.contacts.remove(self.visible()[self.list.currentRow()]); self.refresh()

    def closeEvent(self, e):  # переопределённый компонент 4: отчёт при закрытии
        Report.save(self.login, self.t_in, datetime.now()); e.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    login, ok = QInputDialog.getText(None, "Вход", "Логин:")
    if ok and login.strip():
        window = App(login.strip()); window.show(); sys.exit(app.exec())
