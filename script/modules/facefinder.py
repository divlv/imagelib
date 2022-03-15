#
from modules import ilmodule
import requests
import os
import time
import pickledb
import globals


class FaceFinder(ilmodule.ILModule):
    def __init__(self):
        super().__init__()

        self.people_db = "g:\Projects\imagelib_github\db\people.pdb"
        self.db = pickledb.load(self.people_db, False)

        self.face_api_url_prefix = (
            "https://northeurope.api.cognitive.microsoft.com/face/v1.0"
        )

        self.face_api_service_key = os.environ["AZURE_SERVICE_FACE_API_KEY"]
        self.person_group = "ourfaces"
        self.getMessageBus().subscribe(self.onMessage, globals.TOPIC_FIND_FACE)

    def onMessage(self, arg):
        self.getLogger().debug("Received message: " + str(arg))
        # Prevent too many requests to the API
        self.getLogger().debug(
            "Prevent too many requests to the API. Waiting for 2 seconds..."
        )
        time.sleep(2)
        self.findFacesOnPicture(arg)

    def extractFileName(self, filePath):
        return os.path.basename(filePath)

    def findFacesOnPicture(self, image_data):

        sourceFile = image_data["image_path"]

        self.getLogger().info("Finding faces on picture: " + str(sourceFile))
        self.getLogger().debug("Using people database from: " + self.people_db)

        face_detect_url = self.face_api_url_prefix + "/detect"
        # No "targetFace" means there is only one face detected in the entire image !
        face_identify_url = self.face_api_url_prefix + "/identify"

        params = {"returnFaceId": "true"}

        facesOnPicture = []
        try:
            data = self.getImageData(sourceFile)
            headers = {
                "Content-Type": "application/octet-stream",
                "Ocp-Apim-Subscription-Key": self.face_api_service_key,
            }
            params = {"returnFaceId": "true", "returnFaceLandmarks": "true"}

            response = requests.post(
                face_detect_url, params=params, headers=headers, data=data
            )
            faceIds = []
            if response.status_code == self.HTTP_OK:
                faces = response.json()
                for f in faces:
                    faceIds.append(f["faceId"])
                self.getLogger().debug("Faces on picture:" + str(faceIds))
            else:
                self.getLogger().error("Error finding faces! " + response.text)

            time.sleep(1)
            #
            #
            if len(faceIds) > 0:
                headers = {
                    "Content-Type": "application/json",
                    "Ocp-Apim-Subscription-Key": self.face_api_service_key,
                }

                r = requests.post(
                    face_identify_url,
                    headers=headers,
                    json={
                        "personGroupId": self.person_group,
                        "faceIds": faceIds,
                        "maxNumOfCandidatesReturned": "1",
                        "confidenceThreshold": "0.5",
                    },
                )
                if r.status_code == self.HTTP_OK:
                    self.getLogger().debug("Some face(s) identified.")
                    identifiedFaces = r.json()
                    for idf in identifiedFaces:
                        for candidate in idf["candidates"]:
                            self.getLogger().debug(
                                "Detected: " + self.db.get(candidate["personId"])
                            )
                            facesOnPicture.append(self.db.get(candidate["personId"]))

                    image_data["faces"] = facesOnPicture
                    self.getMessageBus().sendMessage(
                        globals.TOPIC_DESCRIBE_IMAGE, arg=image_data
                    )
                    # self.loop.run_until_complete(
                    #     self.broadcastMessage(globals.TOPIC_DESCRIBE_IMAGE, image_data)
                    # )

                else:
                    self.getLogger().error("Error response code: " + str(r.status_code))
                    self.getLogger().error(r.text)
            else:
                self.getLogger().warning("No faces on photo.")
        except Exception as e:
            self.getLogger().error("Error: " + str(e))
        finally:
            self.cleanupTmp()
