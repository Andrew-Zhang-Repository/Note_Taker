import os
import tempfile
import json
import re
from pathlib import Path
import uuid

class note_store:

    def __init__(self):
        self.path = self.path = Path(os.getenv('APPDATA')) / 'Note_Taker'
        self.config_path = self.path / "default_config.json"
        self.types_dir = self.path / "types" 
        self.config = {}

    def atomic_save(self,data, target_path):

        tmp_path = target_path.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as file:
            json.dump(data, file)

        os.replace(tmp_path, target_path)

    def input_sanitization(self, str_input):

        str_clean = str_input.strip()
        str_clean = re.sub(r'[\\/:*?"<>|]', '_', str_clean)

        return str_clean[:64]

    def registry_management(self):

        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    dict = self.json_dict = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass


    def create_note(self,type_name):
        type_name = self.input_sanitization(type_name)

        if not type_name:
            return False

        for i in self.config["types"]:
            if i == type_name:
                return False

        self.config["types"].append(type_name)
        self.atomic_save(self.config, self.config_path)
        new_file = self.types_dir / f"{type_name}.json"

        initial_data = {
            "name": type_name,
            "notes": []
        }
        
        self.atomic_save(initial_data, new_file)

        return True


    def read_note(self,input_name):

        file_location = self.types_dir / f"{input_name}.json"
        with file_location.open('r', encoding='utf-8') as file:
            data = json.load(file)

        return data["notes"]

    def add_note(self, type_name, note_title, note_body):

        file_location = self.types_dir / f"{type_name}.json"
        with file_location.open('r', encoding='utf-8') as file:
            data = json.load(file)

        insertion = {
            "id": str(uuid.uuid4()),
            "title": note_title,
            "note_body": note_body
        }

        data["notes"].append(insertion)

        self.atomic_save(insertion,file_location)
        
    def delete_note(self,delete_id,type_name):
        
        file_location = self.types_dir / f"{type_name}.json"
        with file_location.open('r', encoding='utf-8') as file:
            data = json.load(file)

        for i in data["notes"]:
            if i["id"] == delete_id:
                data["notes"].pop(i)
                break

        self.atomic_save(data,file_location)

    def update_note(self,id,type_name,new_text):

        file_location = self.types_dir / f"{type_name}.json"
        with file_location.open('r', encoding='utf-8') as file:
            data = json.load(file)

        for i in data["notes"]:
            if i["id"] == id:
                i["note_body"] = new_text
                break

        self.atomic_save(data,file_location)

        





        


        
     



     




