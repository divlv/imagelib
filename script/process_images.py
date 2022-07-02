# Main processing script for the image processing pipeline.

from modules import ilmodule
from modules import facefinder
from modules import thumbnailer
from modules import describeimg
from modules import exifdata
from modules import reversegc
from modules import textonpic
from modules import dateofpic
from modules import databasesaver
from time import sleep
import sys
import glob
import os
import re
import globals
import pika
import json


credentials = pika.PlainCredentials(
    os.environ["RMQ_USERNAME"], os.environ["RMQ_PASSWORD"]
)
parameters = pika.ConnectionParameters(
    os.environ["RMQ_HOST"],
    int(os.environ["RMQ_PORT"]),
    os.environ["RMQ_VIRTUALHOST"],
    credentials,
)
connection = pika.BlockingConnection(parameters)
# Means, how long will live (not received) message in a queue before self-delete
arguments = {"x-message-ttl": int(os.environ["RMQ_TTL"])}

inchannel = connection.channel()
# Binding to message queue
inchannel.queue_declare(
    queue=os.environ["RMQ_IN_QUEUE"], durable=True, arguments=arguments
)

outchannel = connection.channel()
# Binding to message queue
outchannel.queue_declare(
    queue=os.environ["RMQ_OUT_QUEUE"], durable=True, arguments=arguments
)


class Main(ilmodule.ILModule):
    def __init__(self):
        super().__init__()
        # Create all the data processors...
        self.ff = facefinder.FaceFinder()
        self.tt = thumbnailer.Thumbnailer()
        self.di = describeimg.DescribeImage()
        self.ex = exifdata.ExifDataExtractor()
        self.gc = reversegc.ReverseGeoCoder()
        self.tx = textonpic.TextOnPicture()
        self.da = dateofpic.DateOfPicture()
        #
        self.db = databasesaver.Database()

    def run(self):

        self.checkEnvironmentVariableExists("AZURE_SERVICE_DESCRIPTION_KEY")
        self.checkEnvironmentVariableExists("AZURE_SERVICE_FACE_API_KEY")
        self.checkEnvironmentVariableExists("PGHOST")
        self.checkEnvironmentVariableExists("PGPORT")
        self.checkEnvironmentVariableExists("PGUSER")
        self.checkEnvironmentVariableExists("PGPASSWORD")
        self.checkEnvironmentVariableExists("PGDATABASE")

        self.getLogger().info("Starting main loop")

        # Default value for the source directory
        images_dir = globals.pictures_dir_to_detect_faces

        # Images directory can be passed as argument.
        if len(sys.argv) > 1 and sys.argv[1] != "":
            images_dir = sys.argv[1]

        self.getLogger().info("Processing directory: " + images_dir)

        for filename in os.listdir(images_dir):
            if re.match(".*\.png|.*\.jpg|.*\.JPG|.*\.jpeg$", filename):
                image_path = os.path.join(images_dir, filename)

                # self.loop.run_until_complete(
                #     self.broadcastMessage(
                #         globals.TOPIC_THUMBNAIL, {"image_path": image_path}
                #     )
                # )

                # Full processing....
                self.getMessageBus().sendMessage(
                    globals.TOPIC_THUMBNAIL, arg={"image_path": image_path}
                )

                # self.getMessageBus().sendMessage(
                #     globals.TOPIC_DATE, arg={"image_path": image_path}
                # )

        #         thumbnail = thumbnailer.makeImageThumbnail(image_path)

        #         image_data = globals.getImageData(image_path)
        #         params = {}  # passed in URL

        #         # Prevent Error response code:  429 == Too many requests.
        #         face.getLogger().debug(
        #             'Wait 5 seconds. Prevent "Too many requests" error...'
        #         )
        #         time.sleep(5)  # Preserve rate limit...
        #         response = requests.post(
        #             analyze_api_url,
        #             params=params,
        #             headers=headers,
        #             data=image_data,
        #             stream=True,
        #         )

        #         analysis = response.json()

        #         if "error" in analysis:
        #             face.getLogger().error(
        #                 "Error analyzing image: " + analysis["error"]["message"]
        #             )
        #             continue

        #         print(analysis["description"])
        #         # print if captions not empty
        #         imageDescription = ""
        #         if analysis["description"]["captions"]:
        #             imageDescription = analysis["description"]["captions"][0]["text"]

        #         fullGPSdata = dict(ede.getImageGPSData(image_path))
        #         processedGPSdata = {}
        #         for key in fullGPSdata:
        #             if (
        #                 key
        #                 in [
        #                     "GPSLatitudeRef",
        #                     "GPSLatitude",
        #                     "GPSLongitudeRef",
        #                     "GPSLongitude",
        #                     "GPSAltitude",
        #                     "GPSTimeStamp",
        #                     "GPSDateStamp",
        #                 ]
        #                 and fullGPSdata[key] != None
        #             ):
        #                 processedGPSdata[key] = fullGPSdata[key]

        #         processedExifData = {}
        #         try:
        #             imageExif = ede.get_exif(image_path)
        #             processedExifData = ede.get_labeled_exif(imageExif)
        #         except Exception as e:
        #             print("Cannot get EXIF data from file: " + str(image_path))

        #         facesOnPicture = []
        #         facesOnPicture = face.findFacesOnPicture(image_path)

        #         nominatim = {}
        #         if ("GPSLatitude" in fullGPSdata) and ("GPSLongitude" in fullGPSdata):
        #             nominatim = geo.getAddressByGPS(
        #                 fullGPSdata["GPSLatitude"], fullGPSdata["GPSLongitude"]
        #             )

        #         imageDataJSON = {
        #             "filehash": globals.getFileHash(image_path),
        #             "tags": {"tags": analysis["description"]["tags"]},
        #             "faces": {"faces": facesOnPicture},
        #             "nominatim": nominatim,
        #             "originalname": extractFileName(image_path),
        #             "description": imageDescription,
        #         }
        #         imagedb.saveImageData(
        #             imageDataJSON, processedGPSdata, processedExifData, thumbnail
        #         )
        else:
            self.getLogger().info("No [more] images found in directory: " + images_dir)

    def deleteFilesByMask(self, mask):
        for filename in glob.glob(mask):
            os.remove(filename)

    def closeDatabaseIfOpened(self):
        for filename in glob.glob(mask):
            os.remove(filename)


#
# Process single image from RabbitMQ and send result back
#
class QueueProcessor(ilmodule.ILModule):
    def __init__(self):
        super().__init__()
        # Create all the data processors...
        self.ff = facefinder.FaceFinder()
        self.tt = thumbnailer.Thumbnailer()
        self.di = describeimg.DescribeImage()
        self.ex = exifdata.ExifDataExtractor()
        self.gc = reversegc.ReverseGeoCoder()
        self.tx = textonpic.TextOnPicture()
        self.da = dateofpic.DateOfPicture()
        self.ds = databasesaver.Database()

        self.totalReceived = 0
        #

    #
    # Process incoming message with full path to image file
    #
    def processMessage(self, channel, method, properties, messageBytes):
        try:
            messageText = messageBytes.decode("utf-8")

            self.getLogger().info("Received initial data to process: " + messageText)

            dataToProcess = json.loads(messageText)

            # Prepare data for message acknowledgement:
            messageDeliveryTagForAcknowledge = method.delivery_tag
            self.ds.setOutputMQchannelData(channel, messageDeliveryTagForAcknowledge)

            # ...and start Full processing!
            self.getMessageBus().sendMessage(globals.TOPIC_THUMBNAIL, arg=dataToProcess)

            return True
        except Exception as e:
            self.logging.error(str(e))
            self.logging.error(
                "totalReceived = "
                + str(self.totalReceived)
                + "; Error processing incoming message! = "
                + messageBytes.decode("utf-8")
            )
            return False

    #
    # Acknowledge message. i.e. mark message as processed and ready to be purged by RabbitMQ
    #
    def acknowledgeMessage(self, channel, delivery_tag):
        if channel.is_open:
            channel.basic_ack(delivery_tag)
        else:
            self.logging.warning("Cannot acknowledge message. Channel closed.")

    def run(self):

        self.checkEnvironmentVariableExists("AZURE_SERVICE_DESCRIPTION_KEY")
        self.checkEnvironmentVariableExists("AZURE_SERVICE_FACE_API_KEY")

        self.getLogger().info("Starting main loop")

        # Default value for the source directory
        images_dir = globals.pictures_dir_to_detect_faces

        # Images directory can be passed as argument.
        if len(sys.argv) > 1 and sys.argv[1] != "":
            images_dir = sys.argv[1]

        self.getLogger().info("Processing directory: " + images_dir)

        for filename in os.listdir(images_dir):
            if re.match(".*\.png|.*\.jpg|.*\.JPG|.*\.jpeg$", filename):
                image_path = os.path.join(images_dir, filename)

                # self.loop.run_until_complete(
                #     self.broadcastMessage(
                #         globals.TOPIC_THUMBNAIL, {"image_path": image_path}
                #     )
                # )

                # Full processing....
                self.getMessageBus().sendMessage(
                    globals.TOPIC_THUMBNAIL, arg={"image_path": image_path}
                )

                # self.getMessageBus().sendMessage(
                #     globals.TOPIC_DATE, arg={"image_path": image_path}
                # )

        else:
            self.getLogger().info("No [more] images found in directory: " + images_dir)

    def deleteFilesByMask(self, mask):
        for filename in glob.glob(mask):
            os.remove(filename)

    def closeDatabaseIfOpened(self):
        for filename in glob.glob(mask):
            os.remove(filename)


if __name__ == "__main__":
    # main = Main()
    # main.run()
    # main.deleteFilesByMask("./tmb_*.jpg")

    qmain = QueueProcessor()

    # Consuming messages 1 by 1 ...
    inchannel.basic_qos(prefetch_count=1)
    inchannel.basic_consume(
        queue=os.environ["RMQ_IN_QUEUE"],
        auto_ack=False,
        on_message_callback=qmain.processMessage,
    )

    qmain.getLogger().info(" [*] Waiting for messages. To exit press CTRL+C")
    inchannel.start_consuming()
