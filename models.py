from pymongo import MongoClient
import json
import os
import random
from uuid import uuid4
from dotenv import dotenv_values


class Database:
    def __init__(self):
        self.config = dotenv_values(".env")
        self.db = MongoClient(self.config["MONGOURL"]).Dosis
        self.users = self.db.users
        self.blogs = self.db.blogs
        
        
    def makeId(self):
        return "".join(random.sample("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890_", 10))
    
    def addUser(self, email):
        user = {
            "_id": self.makeId(),
            "email": email,
            "name": email.split("@")[0],
            "blood": "",
            "age": 0,
            "contactNumber": 0,
            "gender": "",
            "allergies": [],
            "labReports": [],
            "medicalReports": [],
            "notifications": [],
            "type": "user",
            "doctors": []
        }
        self.users.insert_one(user)
    
    def getUserByEmail(self, email):
        return self.users.find_one({"email": email})
    
    def getUser(self, id):
        return self.users.find_one({"_id": id})
    
    def makeDoctor(self, email):
        self.users.update_one({"email": email}, {"$set": {"type": "doctor", "patients": [], "labReports": [], "medicalReports": []}})
        
    def addPatient(self, id, patient):
        user = self.getUser(id)
        if user:
            if user['type'] == "doctor":
                self.users.update_one({"_id": id}, {"$push": {"patients": patient}})
            else:
                return False
        else:
            return False
        return True
    
    def removePatient(self, id, patient):
        user = self.getUser(id)
        if user:
            if user['type'] == "doctor":
                self.users.update_one({"_id": id}, {"$pull": {"patients": patient}})
            else:
                return False
        else:
            return False
        return True
    
    def addDoctor(self, id, doctor):
        user = self.getUser(id)
        if user:
            if user['type'] == "user":
                self.users.update_one({"_id": id}, {"$push": {"doctors": doctor}})
            else:
                return False
        else:
            return False
        return True
    
    def removeDoctor(self, id, doctor):
        user = self.getUser(id)
        if user:
            if user['type'] == "user":
                self.users.update_one({"_id": id}, {"$pull": {"doctors": doctor}})
            else:
                return False
        else:
            return False
        return True


    def userExists(self, email):
        return self.users.find_one({"email": email}) is not None
    
    def updateUser(self, id, newData):
        self.users.update_one({"_id": id}, {"$set": newData})