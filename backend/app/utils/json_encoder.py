"""
Custom JSON encoder for MongoDB ObjectId and other non-serializable types.
"""
import json
from bson import ObjectId
from datetime import datetime, date

class MongoJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder that handles MongoDB ObjectId, datetime, and date objects.
    """
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)
