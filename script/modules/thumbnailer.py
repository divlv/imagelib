#
import os
import shutil
import time
import requests
import globals
from modules import ilmodule
from unicodedata import normalize

#
# This class is used to extract City, street, etc. name from GPS coordinates
#
#
class Thumbnailer(ilmodule.ILModule):
    def __init__(self):
        super().__init__()
        self.service_key = os.environ["AZURE_SERVICE_DESCRIPTION_KEY"]
        self.thumb_url = "https://northeurope.api.cognitive.microsoft.com/vision/v1.0/generateThumbnail?width=150&height=150&smartCropping=true"

        self.getMessageBus().subscribe(self.onMessage, globals.TOPIC_THUMBNAIL)

    def onMessage(self, arg):
        self.getLogger().debug("Received message: " + str(arg))
        # Prevent too many requests to the API
        self.getLogger().debug(
            "Prevent too many requests to the API. Waiting for 2 seconds..."
        )
        time.sleep(2)
        self.makeImageThumbnail(arg)

    #
    # Creates thumbnail and returns it as byte array
    #
    def makeImageThumbnail(self, image_data):
        sourceFile = image_data["image_path"]
        self.getLogger().debug("Creating thumbnail for: " + sourceFile)
        try:
            data = self.getImageData(sourceFile)
            hash = self.getFileHash(sourceFile)

            headers = {
                # Request headers
                "Content-Type": "application/octet-stream",
                "Ocp-Apim-Subscription-Key": self.service_key,
            }

            r = requests.post(self.thumb_url, headers=headers, data=data, stream=True)

            if r.status_code == 200:
                nameOnly = "./" + os.path.basename(sourceFile).replace(" ", "_")
                fname, ext = os.path.splitext(nameOnly)
                outputThumbnailFile = "./tmb_" + hash + ".jpg"
                with open(outputThumbnailFile, "wb") as f:
                    r.raw.decode_content = True
                    shutil.copyfileobj(r.raw, f)

                self.getLogger().debug("Thumbnail created: " + outputThumbnailFile)

                image_data["thumbnail_path"] = outputThumbnailFile
                image_data["hash"] = hash

                # Attention!!! This looks like NOT ASYNC call!
                # The processing stays in the current context!!! (inside TRY..CATCH!!!)
                self.getMessageBus().sendMessage(
                    globals.TOPIC_FIND_FACE, arg=image_data
                )

                # self.loop.run_until_complete(
                #     self.broadcastMessage(globals.TOPIC_FIND_FACE, image_data)
                # )

                # return self.get_bytes_from_file(outputThumbnailFile)
            else:
                self.getLogger().error(
                    "Thumbnail creation failed: " + str(r.status_code)
                )
        except Exception as e:
            self.getLogger().error("Thumbnail creation exception: " + str(e))
