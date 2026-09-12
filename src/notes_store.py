import os
import tempfile
import json
import re
from pathlib import Path
import uuid

class note_store:

    def __init__(self):


        self.path = Path(os.getenv('APPDATA')) / 'Note_Taker'
        
        self.config_path = self.path / "default_config.json"
        self.types_dir = self.path / "types"
        self.config = {}
        
        self.registry_management()

        with open(self.config_path, "r") as file:
            self.config_settings  = json.load(file)

        self.image_dir = self.path / "app_images"
        if not os.path.exists(self.image_dir):
            os.makedirs(self.image_dir)

    def registry_management(self):
       
        self.path.mkdir(parents=True, exist_ok=True)
        self.types_dir.mkdir(parents=True, exist_ok=True)

        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.config = {}
        
        if not self.config or "types" not in self.config:
            self.config = {
                "types": ["General"],
                "api_key": "",
                "default_model": "gemini-1.5-flash",
                "ui_settings": {
                    "main": { "opacity": 0.85, "bg_color": "#1e1b2e", "text_color" :"#ebeaf3" },
                    "popout": { "opacity": 1.0, "bg_color": "#1e1b2e", "text_color" :"#ebe9f1"},
                    "llm": { "opacity": 0.70, "bg_color": "#1e1b2e", "text_color" :"#efeef1"}
                }
            }
           
            self.atomic_save(self.config, self.config_path)
            
            initial_data = {"name": "General", "notes": []}
            self.atomic_save(initial_data, self.types_dir / "General.json")

    def create_new_type(self,name):

        safe_name = re.sub(r'[\\/*?:"<>|]', "", name).strip()
    
        if not safe_name:
            print("Error: Name cannot be empty or just special characters.")
            return False
            
        dir_path = Path(self.types_dir)
        file_path = dir_path / f"{safe_name}.json"
        
        if file_path.exists():
            print(f"Error: A category named '{safe_name}' already exists.")
            return False
            
        initial_data = {"name": safe_name, "notes": []}
        self.atomic_save(initial_data, file_path)
        
        if not hasattr(self, 'active_types'):
            self.active_types = []
        if safe_name not in self.active_types:
            self.active_types.append(safe_name)
            
        return True
        


    def atomic_save(self,data, target_path):

        tmp_path = target_path.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as file:
            json.dump(data, file)

        os.replace(tmp_path, target_path)

    def input_sanitization(self, str_input):

        str_clean = str_input.strip()
        str_clean = re.sub(r'[\\/:*?"<>|]', '_', str_clean)

        return str_clean[:64]



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

        self.atomic_save(data,file_location)
        
    def delete_note(self,delete_id,type_name):
        
        file_location = self.types_dir / f"{type_name}.json"
        with file_location.open('r', encoding='utf-8') as file:
            data = json.load(file)

        for i in range(len(data["notes"]) - 1, -1, -1):
            if data["notes"][i]["id"] == delete_id:
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

        





        


        
     



     




