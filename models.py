from pymongo import MongoClient
import json
import os
import random
from uuid import uuid4
from datetime import datetime
import os

class Database:
    def __init__(self, storage):
        self.db = MongoClient(os.getenv("MONGOURL")).Dosis
        self.users = self.db.users
        self.blogs = self.db.blogs
        self.blogs = self.db.blogs
        self.storage = storage
        
    def makeId(self, length = 24):
        return "".join(random.sample("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890_", length))
    
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
    
    def addMedicalReport(self, report):
        user = self.getUser(report["by"])
        report["_id"] = self.makeId()
        if user:
            if user['type'] == "doctor":
                self.users.update_one({"_id": report["by"]}, {"$push": {"medicalReports": report}})
                self.users.update_one({"_id": report["for"]}, {"$push": {"medicalReports": report, "notifications": {"type": "medicalReport", "report": report}}})
            else:
                return False
        else:
            return False
        return True

    def getMedicalReport(self, id, reportID):
        user = self.getUser(id)
        if user:
            reports = self.users.find_one({"_id": id})["medicalReports"]
            report = None
            for r in reports:
                if r["_id"] == reportID:
                    report = r
            if report:
                report["by"] = self.getUser(report["by"])
                report["for"] = self.getUser(report["for"])
                return report
            return False
        return False
    
    def addLabReport(self, report):
        user = self.getUser(report["by"])
        report["_id"] = self.makeId(30)
        if user:
            if user['type'] == "doctor":
                self.storage.child("labReports/"+report["_id"]+"."+report["fileLink"].filename.split('.')[-1]).put(report["fileLink"])
                report["fileLink"] = self.storage.child("labReports/"+report["_id"]+"."+report["fileLink"].filename.split('.')[-1]).get_url(None)
                self.users.update_one({"_id": report["by"]}, {"$push": {"labReports": report}})
                self.users.update_one({"_id": report["for"]}, {"$push": {"labReports": report, "notifications": {"type": "labReport", "report": report}}})
                return report["_id"]
            else:
                return False
        else:
            return False
        return True

    def getLabReport(self, id, reportID):
        user = self.getUser(id)
        if user:
            reports = self.users.find_one({"_id": id})["labReports"]
            report = None
            for r in reports:
                if r["_id"] == reportID:
                    report = r
            if report:
                report["by"] = self.getUser(report["by"])
                report["for"] = self.getUser(report["for"])
                return report
            return False
        return False
    
    def getNotifications(self, id):
        user = self.getUser(id)
        if user['type']=="user":
            notifs = []
            notifications = user["notifications"]
            for notification in notifications:
                if notification['type'] == "labReport":
                    notifs.append({'type': 'labReport', 'report': {"heading": notification['report']['heading'], "date": notification['report']['on'], "_id": notification['report']['_id']}})
                if notification['type'] == "medicalReport":
                    notifs.append({'type': 'medicalReport', 'report': {"heading": notification['report']['heading'], "date": notification['report']['on'], "_id": notification['report']['_id']}})
            return notifs[::-1]
        
    def getBlogs(self, id):
        return [blog for blog in self.blogs.find({"by._id": id})]
    
    def addBlog(self, data, id):
        user = self.getUser(id)
        data['_id'] = self.makeId()
        data['by'] = user
        self.blogs.insert_one(data)
        
    def getBlog(self, id):
        return self.blogs.find_one({"_id": id})