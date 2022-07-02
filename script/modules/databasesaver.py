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

        self.outputMQchannel = None
        self.delivery_tag = None

    def setOutputMQchannelData(self, outputMQchannel, deliveryTag):
        self.outputMQchannel = outputMQchannel
        self.delivery_tag = deliveryTag

    def acknowledgeMessage(self):
        if self.outputMQchannel.is_open:
            self.outputMQchannel.basic_ack(self.delivery_tag)
        else:
            self.logging.warning("Cannot acknowledge message. Channel closed.")

    def onMessage(self, arg):
        self.getLogger().debug("Received database save request")

        self.saveImageData(arg)

        self.outputMQchannel.basic_publish(
            exchange=os.environ["RMQ_EXCHANGE"],
            routing_key="imagedatakey",
            body=json.dumps(arg),
        )

        # Mark incoming message as PROCESSED and purge ot from the Queue:
        self.acknowledgeMessage()

        # self.getMessageBus().sendMessage(globals.TOPIC_???????, arg=metadata)

    #
    # Save image metadata to PostgreSQL database
    #
    def saveImageData(self, imageDataJSON):

        dbConnection = self.connectionPool.getconn()

        try:
            dbCursor = dbConnection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            )
            # Delete old data, if exists
            imageSha256 = imageDataJSON["hash"]
            if not self.saveDuplicateImageData:
                dbCursor.execute(
                    "DELETE FROM image_lib WHERE left(filehash, 2)=%s AND filehash=%s",
                    (imageSha256[:2], imageSha256),
                )

            if (
                "GPSLatitude" in imageDataJSON["gps"]
                and imageDataJSON["gps"]["GPSLatitude"]
            ):
                GPSLatitude = imageDataJSON["gps"]["GPSLatitude"]
            else:
                GPSLatitude = None

            if (
                "GPSLongitude" in imageDataJSON["gps"]
                and imageDataJSON["gps"]["GPSLongitude"]
            ):
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
            sourcepath = imageDataJSON["image_path"]

            fullDate = None
            if imageDataJSON["dateOfImage"]:
                d = time.strptime(imageDataJSON["dateOfImage"], "%Y:%m:%d %H:%M:%S")
                fullDate = time.strftime("%Y-%m-%d %H:%M:%S", d)

            imageYear = None
            imageMonth = None
            imageDay = None

            if "remote_id" in imageDataJSON:
                remote_id = imageDataJSON["remote_id"]
            else:
                remote_id = None
            # remote_url
            if "remote_url" in imageDataJSON:
                remote_url = imageDataJSON["remote_url"]
            else:
                remote_url = None

            image_data = imageDataJSON

            faces = " ".join(image_data["faces"])

            if "display_name" in image_data:
                whereisit = image_data["display_name"]
            else:
                whereisit = ""

            if "dateOfImage" in image_data:
                whenitwas = image_data["dateOfImage"]
            else:
                whenitwas = ""

            tags = " ".join(image_data["tags"])

            if "description" in image_data:
                description = image_data["description"]
            else:
                description = ""

            if "EXIF" in image_data and "Make" in image_data["EXIF"]:
                camera = image_data["EXIF"]["Make"]
            else:
                camera = ""

            if "EXIF" in image_data and "Model" in image_data["EXIF"]:
                cameraModel = image_data["EXIF"]["Model"]
            else:
                cameraModel = ""

            shorthash = image_data["hash"][:7].upper()

            if "text_en" in image_data:
                texten = image_data["text_en"]
            else:
                texten = ""

            if "text_ru" in image_data:
                textru = image_data["text_ru"]
            else:
                textru = ""

            filledStringsStack = []
            if faces.strip() != "":
                filledStringsStack.append(faces.strip())
            if whereisit.strip() != "":
                filledStringsStack.append(whereisit.strip())
            if whenitwas.strip() != "":
                filledStringsStack.append(whenitwas.strip())
            if tags.strip() != "":
                filledStringsStack.append(tags.strip())
            if description.strip() != "":
                filledStringsStack.append(description.strip())
            if camera.strip() != "":
                filledStringsStack.append(camera.strip())
            if cameraModel.strip() != "":
                filledStringsStack.append(cameraModel.strip())
            if shorthash.strip() != "":
                filledStringsStack.append(shorthash.strip())
            if texten.strip() != "":
                filledStringsStack.append(texten.strip())
            if textru.strip() != "":
                filledStringsStack.append(textru.strip())

            searchtext = " ".join(filledStringsStack)

            # Generate GUID for DB record
            guid = uuid.uuid1()
            dbCursor.execute(
                "INSERT INTO image_lib (guid, remote_id, remote_url, searchtext, filehash, gpsdata, exifdata, latitude, longitude, address, address_full, faces, tags, originalname, sourcepath, description, thumbnail, imagedate, taken_at, imageyear, imagemonth, imageday) VALUES ("
                "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    str(guid),
                    remote_id,
                    remote_url,
                    searchtext,
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
                    sourcepath,
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
            self.getLogger().debug("Data saved with GUID: " + str(guid))
        except Exception as e:
            dbConnection.rollback()
            # log.error("{} error: {}".format(func.__name__, e))
            print(e)
            # Throw exception to caller
            raise e
        finally:
            self.connectionPool.putconn(dbConnection)
        return
