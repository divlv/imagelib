# Main processing script for the image processing pipeline.

from modules import ilmodule
from modules import facefinder
from modules import thumbnailer
from modules import describeimg
from modules import exifdata
import sys
import os
import re
import globals
import asyncio


class Main(ilmodule.ILModule):
    def __init__(self):
        super().__init__()
        self.ff = facefinder.FaceFinder()
        self.tt = thumbnailer.Thumbnailer()
        self.di = describeimg.DescribeImage()
        self.ex = exifdata.ExifDataExtractor()

    def run(self):

        self.checkEnvironmentVariableExists("AZURE_SERVICE_DESCRIPTION_KEY")
        self.checkEnvironmentVariableExists("AZURE_SERVICE_FACE_API_KEY")
        self.checkEnvironmentVariableExists("POSTGRES_HOST")
        self.checkEnvironmentVariableExists("POSTGRES_PORT")
        self.checkEnvironmentVariableExists("POSTGRES_USER")
        self.checkEnvironmentVariableExists("POSTGRES_PASSWORD")
        self.checkEnvironmentVariableExists("POSTGRES_DB")

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

                self.getMessageBus().sendMessage(globals.TOPIC_THUMBNAIL, arg={"image_path": image_path})


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
        # else:
        #     face.getLogger().info("No [more] images found in directory: " + images_dir)


if __name__ == "__main__":
    main = Main()
    main.run()
