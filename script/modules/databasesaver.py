#
from modules import ilmodule
import time
import uuid
import json
import os
import psycopg2
import psycopg2.extras
from psycopg2 import pool


import globals

#
# Module for saving data to database
#
class Database(ilmodule.ILModule):
    def __init__(self):
        super().__init__()

        minConnection = 1
        maxConnection = 2
        self.connectionPool = psycopg2.pool.ThreadedConnectionPool(
            minConnection,
            maxConnection,
            user=os.getenv("PGUSER"),
            password=os.getenv("PGPASSWORD"),
            host=os.getenv("PGHOST"),
            port=os.getenv("PGPORT"),
            database=os.getenv("PGDATABASE"),
        )
        if self.connectionPool:
            print("DB Connection pool created successfully")

        # By default DO NOT save DUPLICATES!
        self.saveDuplicateImageData = False
        
        self.getMessageBus().subscribe(self.onMessage, globals.TOPIC_SAVEDB)

    def onMessage(self, arg):
        self.getLogger().debug("Received database save request")

        self.saveImageData(arg)
        # self.getMessageBus().sendMessage(globals.TOPIC_???????, arg=metadata)

    #
    # Save image metadata to PostgreSQL database
    #
    def saveImageData(self, imageDataJSON):

        dbConnection = self.connectionPool.getconn()

        try:
            dbCursor = dbConnection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            # Delete old data, if exists
            imageSha256 = imageDataJSON["hash"]
            if not self.saveDuplicateImageData:
                dbCursor.execute(
                    "DELETE FROM image_lib WHERE left(filehash, 2)=%s AND filehash=%s",
                    (imageSha256[:2], imageSha256),
                )

            if "GPSLatitude" in imageDataJSON["gps"] and imageDataJSON["gps"]["GPSLatitude"]:
                GPSLatitude = imageDataJSON["gps"]["GPSLatitude"]
            else:
                GPSLatitude = None

            if "GPSLongitude" in imageDataJSON["gps"] and imageDataJSON["gps"]["GPSLongitude"]:
                GPSLongitude = imageDataJSON["gps"]["GPSLongitude"]
            else:
                GPSLongitude = None

            address = {}
            if "address" in imageDataJSON:
                address = imageDataJSON["address"]

            display_name = ""
            if "display_name" in imageDataJSON:
                display_name = imageDataJSON["display_name"]

            thumbnailBytes = self.get_bytes_from_file(imageDataJSON["thumbnail_path"])

            originalname = os.path.basename(imageDataJSON["image_path"])

            fullDate = None
            if imageDataJSON["dateOfImage"]:
                d = time.strptime(imageDataJSON["dateOfImage"], "%Y:%m:%d %H:%M:%S")
                fullDate = time.strftime('%Y-%m-%d %H:%M:%S', d)

            imageYear = None
            imageMonth = None
            imageDay = None

            # Generate GUID for DB record
            guid = uuid.uuid1()
            dbCursor.execute(
                "INSERT INTO image_lib (guid, filehash, gpsdata, exifdata, latitude, longitude, address, address_full, faces, tags, originalname, description, thumbnail, imagedate, taken_at, imageyear, imagemonth, imageday) VALUES ("
                "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    str(guid),
                    str(imageSha256),
                    json.dumps(imageDataJSON["gps"]),
                    json.dumps(imageDataJSON["EXIF"]),
                    GPSLatitude,
                    GPSLongitude,
                    json.dumps(address),
                    display_name,
                    json.dumps(imageDataJSON["faces"]),
                    json.dumps(imageDataJSON["tags"]),
                    originalname,
                    imageDataJSON["description"],
                    thumbnailBytes,
                    fullDate,
                    fullDate,
                    imageYear,
                    imageMonth,
                    imageDay,





                ),
            )

            dbConnection.commit()
            dbCursor.close()
            print("Data saved with GUID: " + str(guid))
        except Exception as e:
            dbConnection.rollback()
            # log.error("{} error: {}".format(func.__name__, e))
            print(e)
            # Throw exception to caller
            raise e
        finally:
            self.connectionPool.putconn(dbConnection)
        return