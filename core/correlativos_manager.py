import os
import json
from PyQt6.QtCore import QDate

class CorrelativosManager:
    """Gestor global de números correlativos."""
    
    def __init__(self, agenda_path: str):
        self.agenda_path = agenda_path
        self.data_path = os.path.join(agenda_path, 'correlativos.json')
        self.types = {}
        self._load()

    def _load(self):
        if not self.agenda_path:
            return
            
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    self.types = json.load(f)
            except Exception as e:
                print(f"[CorrelativosManager] Error loading data: {e}")
        else:
            self._migrate_old_laboratorio()

    def _migrate_old_laboratorio(self):
        # Migration from old laboratorio/correlativos.json
        old_path = os.path.join(self.agenda_path, 'laboratorio', 'correlativos.json')
        if os.path.exists(old_path):
            try:
                with open(old_path, 'r', encoding='utf-8') as f:
                    old_data = json.load(f)
                
                # Find the max count from old data
                max_count = max(old_data.values()) if old_data else 0
                self.types["Check List"] = {
                    "prefix": "",
                    "counts": {"GLOBAL": max_count}
                }
                self.save()
            except Exception as e:
                print(f"[CorrelativosManager] Error migrating old data: {e}")
        
        # Ensure default types exist if not present
        if "Check List" not in self.types:
            self.types["Check List"] = {"prefix": "", "counts": {"GLOBAL": 0}}
        if "Información" not in self.types:
            self.types["Información"] = {"prefix": "INFO", "counts": {"GLOBAL": 0}}
        self.save()

    def save(self):
        if not self.agenda_path:
            return
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
        try:
            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump(self.types, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[CorrelativosManager] Error saving data: {e}")

    def get_types(self) -> list:
        return list(self.types.keys())

    def get_type_info(self, name: str) -> dict:
        return self.types.get(name, {})

    def add_or_update_type(self, name: str, prefix: str):
        if name not in self.types:
            self.types[name] = {"prefix": prefix, "counts": {"GLOBAL": 0}}
        else:
            self.types[name]["prefix"] = prefix
        self.save()

    def delete_type(self, name: str):
        if name in self.types:
            del self.types[name]
            self.save()

    def reset_counters(self, name: str):
        if name in self.types:
            self.types[name]["counts"] = {}
            self.save()

    def get_next_serial_info(self, name: str, date: QDate = None) -> tuple:
        """Returns (yymm_key, current_count, formatted_serial_string)"""
        if date is None:
            date = QDate.currentDate()
            
        yy = date.toString("yy")
        mm = date.toString("MM")
        yymm = f"{yy}{mm}"
        global_key = "GLOBAL"
        
        if name not in self.types:
            prefix_val = "INFO" if name == "Información" else ""
            self.add_or_update_type(name, prefix_val)

        type_data = self.types.get(name, {"prefix": "", "counts": {"GLOBAL": 0}})
        counts = type_data.get("counts", {})
        
        count = counts.get(global_key, 0) + 1
        key = global_key
            
        if count > 999:
            count = 1
            
        prefix = type_data.get("prefix", "")
        serial_str = f"{prefix}{yymm}{count:03d}"
            
        return key, count, serial_str

    def commit_serial(self, name: str, key: str, count: int):
        if name in self.types:
            self.types[name].setdefault("counts", {})[key] = count
            self.save()
