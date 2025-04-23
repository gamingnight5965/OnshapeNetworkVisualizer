from typing import Annotated, Literal, Optional
from onshape_api.base import BASE_URL, BaseOnshapeAPI, api_request
import json
import requests


class OnshapeAssemblyAPI(BaseOnshapeAPI):
    def __init__(self, access_key: str, private_key: str):
        super().__init__(access_key, private_key, "assemblies")

    @api_request
    def get_definition(
        self,
        document_id: str,
        wvm: Literal["w", "v", "m"],
        wvm_id: Annotated[str, "Id for (w)orkspace, (v)ersion, or (m)icroversion"],
        element_id: str,
        link_docuemt_id: Optional[str] = None,
        configuration: Annotated[
            Optional[str],
            "URL-encoded string of configuration values (separated by ';'). See the [configutation API Guide](https://onshape-public.github.io/docs/api-adv/configs/)",
        ] = None,
        exploded_view_id: Optional[str] = None,
        include_mate_features: bool = False,
        include_non_solids: bool = False,
        include_mate_connectors: bool = False,
        exclude_suppressed: bool = False,
    ):
        request_url = f"{BASE_URL}/{self._url_extension}/d/{document_id}/{wvm}/{wvm_id}/e/{element_id}"
        payload: dict = {
            "includeMateFeatures": include_mate_features,
            "includeNonSolids": include_non_solids,
            "includeMateCOnnectors": include_mate_connectors,
            "excludeSuppressed": exclude_suppressed,
        }

        if link_docuemt_id is not None:
            payload["linkDocumentId"] = link_docuemt_id
        if configuration is not None:
            payload["configuration"] = configuration
        if exploded_view_id is not None:
            payload["explodedViewId"] = exploded_view_id

        return self.session.get(request_url, params=payload, auth=self._auth)
