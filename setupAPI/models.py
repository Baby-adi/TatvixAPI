import mongoengine as me
from datetime import datetime,timezone
import uuid

class PDFImage(me.DynamicDocument):
    filename = me.StringField(required=True)  # Store filename
    file = me.FileField(required=True)  # Store image in GridFS
    image_id = me.UUIDField(required=True,default=uuid.uuid4,binary=False) # Generate a unique id for each image

class ExtractedText(me.DynamicDocument):
    image = me.ReferenceField(PDFImage)  # Link to image
    text = me.StringField(required=True)
    time_stamp = me.DateTimeField(default=lambda: datetime.now(timezone.utc))  # Store timestamp of extraction
