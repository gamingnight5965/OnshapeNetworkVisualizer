from onshape_api.assemblies import OnshapeAssemblyAPI
from onshape_api.documents import OnshapeDocumentAPI
from onshape_api.partstudio import OnshapePartStudioAPI
from onshape_api.base import BaseOnshapeAPI


class OnshapeAPI:
    def __init__(self, access_key: str, private_key: str):
        self.assembly = OnshapeAssemblyAPI(access_key, private_key)
        self.part_studio = OnshapePartStudioAPI(access_key, private_key)
        self.document = OnshapeDocumentAPI(access_key, private_key)
