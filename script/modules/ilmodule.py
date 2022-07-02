#
import logging
from PIL import Image
from resizeimage import resizeimage
import os
import hashlib

# import asyncio

# Using Publish-Subscribe pattern to decouple the processing code
from pubsub import pub

# import nest_asyncio


# The ILModule is a basic class for all the objects that are used in the Image Library project
class ILModule:
    def __init__(self):
        self.log = logging.getLogger(self.__class__.__name__)

        LOGLEVEL = os.environ.get("LOGLEVEL", "INFO").upper()
        logging.basicConfig(
            format="%(levelname)s: %(filename)s:%(lineno)s %(funcName)s: %(message)s",
            level=LOGLEVEL,
        )

        self.tmp_file = "./~tmp.jpg"
        self.max_file_size = 2000000
        self.picture_resize_width = 1024

        self.HTTP_OK = 200
        # Enable nested loops
        # nest_asyncio.apply()

        # self.loop = asyncio.new_event_loop()
        # asyncio.set_event_loop(self.loop)

        self.pub = pub

    # async def broadcastMessage(self, topic, data):
    #     self.getMessageBus().sendMessage(topic, arg=data)

    def get_bytes_from_file(self, filename):
        return open(filename, "rb").read()

    def getLogger(self):
        return self.log

    def getMessageBus(self):
        return self.pub

    def saveJsonToFile(self, json, filename):
        """
        Save a json object to a file
        """
        with open(filename, "w") as f:
            f.write(json)

    def getImageData(self, sourceFile):
        """
        Reads the image file and returns the image meta-data.

        The function returns

        :param sourceFile: The path to the image file you want to upload
        :return: The image data.
        """
        data = open(sourceFile, "rb").read()
        if len(data) > self.max_file_size:
            self.log.debug(
                "Image file size is bigger than "
                + str(self.max_file_size)
                + " => "
                + str(len(data))
                + "bytes. Needs to resize.."
            )

            img = Image.open(sourceFile)
            img = resizeimage.resize_width(img, self.picture_resize_width)
            img.save(self.tmp_file, img.format)
            data = open(self.tmp_file, "rb").read()
            self.log.debug("Resized to " + str(len(data)) + "bytes")

        return data

    def getFileHash(self, filePath):
        """
        Given a file path, return the SHA256 hash of the file

        :param filePath: The path to the file you want to upload
        :return: a dictionary with the file name and the hash.
        """
        sha = hashlib.sha256()
        BUF_SIZE = 65536  # lets read stuff in 64kb chunks!
        with open(filePath, "rb") as f:
            while True:
                data = f.read(BUF_SIZE)
                if not data:
                    break
                sha.update(data)
        return sha.hexdigest()

    def cleanupTmp(self):
        """
        Remove the temporary file
        """
        # Cleanup tmp file
        try:
            os.remove(self.tmp_file)
        except:
            # TMP file was not created
            pass

    def checkEnvironmentVariableExists(self, envVarName):
        if envVarName in os.environ and not os.environ[envVarName] == "":
            return True
        else:
            print("Environment variable: %s is needed" % envVarName)
            exit(1)
