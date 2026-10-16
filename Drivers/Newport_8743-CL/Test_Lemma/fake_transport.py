"""Faux transport minimal pour tester le driver sans matériel. Pas un simulateur de contrôleur :
il garde VA, AC, QM par axe, répond comme les mesures du 2026-10-14 et enregistre tout ce qui est envoyé."""
import re


class FakeTransport:
    def __init__(self, qm: int = 0):
        self.sent, self.errors = [], []
        self.val = {f"{a}{m}": v for a in "1234" for m, v in (("VA", 2000), ("AC", 100000), ("QM", qm))}

    def write(self, cmd):
        self.sent.append(cmd)
        m = re.fullmatch(r"(\d)(VA|AC|QM)(-?\d+)", cmd)
        if m:
            self.val[m.group(1) + m.group(2)] = int(m.group(3))
            if m.group(2) == "VA" and int(m.group(3)) > 2000:
                self.errors.append(f"{m.group(1)}10, MAXIMUM VELOCITY EXCEEDED")

    def ask(self, cmd):
        self.sent.append(cmd)
        if cmd == "*IDN?":
            return "New_Focus 8742 v3.04 09/09/16 108042"
        if cmd == "TB?":
            return self.errors.pop(0) if self.errors else "0, NO ERROR DETECTED"
        m = re.fullmatch(r"(\d)(VA|AC|QM)\?", cmd)
        if m:
            return str(self.val[m.group(1) + m.group(2)])
        if re.fullmatch(r"\d(TP|MD)\?", cmd):
            return "0" if cmd[1:3] == "TP" else "1"
        raise AssertionError(f"requête inattendue : {cmd}")

    def close(self):
        pass


class FakeTransport8743:
    """Faux transport minimal du 8743-CL : valeurs par défaut mesurées le 2026-10-15 (8311 sur l'axe 1).
    Garde VA, AC, QM, SN, MM, CL, DB, FE par axe et enregistre tout ce qui est envoyé. Pas de dynamique de mouvement."""

    def __init__(self, qm=0, zz=0, sn=1, zh1=4):
        self.sent, self.errors = [], []
        self.val = {}
        for a in "12":
            self.val.update({f"{a}VA": 2000, f"{a}AC": 100000, f"{a}QM": qm, f"{a}SN": sn, f"{a}MM": 0,
                             f"{a}CL": "0.1000", f"{a}DB": 0, f"{a}FE": 1000, f"{a}ZH": zh1 if a == "1" else 0,
                             f"{a}TP": 0, f"{a}MD": 1, f"{a}OF": 0, f"{a}AF": 1})
        self.zz, self.ph = zz, 56

    def write(self, cmd):
        self.sent.append(cmd)
        m = re.fullmatch(r"([12])(VA|AC|QM|SN|MM|CL|DB|FE)(-?[\d.]+)", cmd)
        if m:
            cle, v = m.group(1) + m.group(2), m.group(3)
            self.val[cle] = v if m.group(2) == "CL" else int(v)
            if m.group(2) == "VA" and int(v) > 2000:
                self.errors.append(f"{m.group(1)}10, MAXIMUM VELOCITY EXCEEDED")
            return
        m = re.fullmatch(r"([12])PR(-?\d+)", cmd)
        if m:
            self.val[m.group(1) + "TP"] += int(m.group(2))

    def ask(self, cmd):
        self.sent.append(cmd)
        if cmd == "*IDN?":
            return "New_Focus 8743-CL v4.06 01/19/17 13097"
        if cmd == "TB?":
            return self.errors.pop(0) if self.errors else "0, NO ERROR DETECTED"
        if cmd == "ZZ?":
            return str(self.zz)
        if cmd == "PH?":
            return str(self.ph)
        m = re.fullmatch(r"([12])(VA|AC|QM|SN|MM|CL|DB|FE|ZH|TP|MD|OF|AF)\?", cmd)
        if m:
            return str(self.val[m.group(1) + m.group(2)])
        raise AssertionError(f"requête inattendue : {cmd}")

    def close(self):
        pass
