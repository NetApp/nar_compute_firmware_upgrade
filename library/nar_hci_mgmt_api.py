#!/usr/bin/python

# (c) 2018-2019, NetApp, Inc
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from copy import deepcopy
import json
import logging
import typing as t

from ansible.module_utils.basic import AnsibleModule
from envparse import env
import requests
from requests_oauthlib.oauth2_session import OAuth2Session, TokenExpiredError


ANSIBLE_METADATA = {"metadata_version": "1.1", "status": ["preview"], "supported_by": "certified"}

DOCUMENTATION = """

module: nar_hci_mgmt_api

short_description: Execute mNode API

# To be changed / removed
# extends_documentation_fragment:
# version_added:
# author:

description:
- Execute mNode API

options:

  url:
    description:
      - mNode URL in the form (http://service/path).
    required: true

  data:
    description:
      - The json-data of the request to the service.
    required: false
    default: null

  method:
    description:
      - The HTTP method of the request. It MUST be uppercase.
    required: false
    choices: [ "GET", "POST", "PUT", "DELETE" ]
    default: "GET"

  config_path:
    description:
      - Auth Config file path.
    required: false

  auth_skip:
    description:
      - Skip auth or not.
    required: false
    choices: ["True", "False"]
    default: "False"
"""

EXAMPLES = """
- name: New mnode module
   nar_hci_mgmt_api:
     url: https://service/path
     data:
       ip: ip
       type: type
       host_name: host
       config: {}
     method: POST
"""

RETURN = """
"""

AUTH_CONFIG_PATH = env.str(
    "AUTH_CONFIG_PATH",
    default="config/config.json"
)


logger = logging.getLogger(__name__)


class MNodeSession(OAuth2Session):
    """
    MNodeSession is a subclass of OAuth2Session that provides token authentication for MNode
    clients.

    It implements automatic token refresh via a re-authentication call whenever a token expires or a
    request fails with a 401 error.
    """

    def __init__(
        self,
        token_url: str,
        client_id: str,
        username: str,
        password: str,
        verify: bool,
        auth_skip: bool,
    ):

        super().__init__()

        self._client_id = client_id
        self._token_url = token_url
        self._username = username
        self._password = password
        self._verify = verify
        self._auth_skip = auth_skip

    def fetch_token(self) -> dict:
        """Fetch and set auth token using client credentials."""
        payload = {
            "grant_type": "password",
            "client_id": self._client_id,
            "username": self._username,
            "password": self._password,
        }

        response = super().request("POST", self._token_url, data=payload, verify=self._verify)
        response.raise_for_status()

        self.token = response.json()
        return self.token

    def request(self, method: str, url: str, **kwargs: t.Any) -> requests.Response:
        """Intercept all requests and add or regenerate the auth token if token isn't set or if
        request fails with 401 status."""
        if self._auth_skip:
            return super().request(method, url, **kwargs)

        if not self.token:
            # Bootstrap first token if we haven't fetched one yet.
            self.fetch_token()

        # Allow for a single token refresh if token expires or request fails with 401.
        tried_refresh = False

        while True:
            try:
                resp = super().request(method, url, **kwargs)
            except TokenExpiredError:
                if tried_refresh:
                    # Raise if we already attempted to refresh the token.
                    raise
                resp = None

            if (resp is None or resp.status_code == 401) and not tried_refresh:
                # Fetch a brand new token since MNode auth provider doesn't support refresh tokens.
                self.fetch_token()
                tried_refresh = True
            else:
                # Coverage doesn't properly record that we got here due to standalone break.
                break  # pragma: no cover

        return resp


def create_mnode_session(
    config_file: t.Optional[str] = None,
    auth_skip: t.Optional[bool] = None,
    username: t.Optional[str] = None,
    password: t.Optional[str] = None,
    verify: bool = False,
) -> t.Union[MNodeSession, requests.Session]:
    """Return MNode session for making HTTP requests to MNode services from another service."""
    if auth_skip is None:
        auth_skip = False

    if auth_skip:
        session = requests.Session()
        session.verify = verify
        return session

    if config_file is None:
        config_file = AUTH_CONFIG_PATH

    config = load_client_config(config_file)
    token_url = config.get("token_url", "")
    client_id = config.get("client_id", "")

    if not token_url:
        raise ValueError("Missing 'token_url' in MNode client config file")

    session = MNodeSession(token_url, client_id=client_id, username=username, password=password,
                           verify=verify, auth_skip=auth_skip)
    session.verify = verify
    return session


def load_client_config(config_file: str) -> t.Dict[str, t.Any]:
    """Return client config from file."""
    try:
        with open(config_file) as fp:
            return json.load(fp)
    except OSError as exc:  # pragma: no cover
        logger.exception("Unable to open client config file {config_file!r}: {exc}")
        raise
    except json.JSONDecodeError as exc:  # pragma: no cover
        logger.exception("Unable to parse client config file {config_file!r} as JSON: {exc}")
        raise


def execute_mnode_api():
    # Setting `username` and `password` as optional fields because these parameters are not
    # required while `auth_skip=True`.
    argument_spec = {
        "config_path": dict(required=False, type="str", default=AUTH_CONFIG_PATH),
        "auth_skip": dict(required=False, type="bool", default=False),
        "method": dict(required=False, default="GET", choices=["GET", "POST", "PUT", "DELETE"]),
        "data": dict(required=False, default=None, type="raw"),
        "username": dict(required=False, type="str", default=""),
        "password": dict(required=False, type="str", default=""),
        "verify": dict(required=False, type="bool", default=False),
        "timeout": dict(required=False, type="int", default=60),
        "url": dict(required=True),
    }

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    url = module.params["url"]
    data = module.params["data"]
    method = module.params["method"]
    auth_skip = module.params["auth_skip"]
    config_path = module.params["config_path"]
    username = module.params["username"]
    password = module.params["password"]
    verify = module.params["verify"]
    timeout = module.params["timeout"]

    # Preparing invocation data manually to hide `username` and `password` from the log
    params = deepcopy(module.params)
    params.pop("username", None)
    params.pop("password", None)
    invocation = {"module_args": params}

    try:
        mnode_session = create_mnode_session(
            config_file=config_path,
            auth_skip=auth_skip,
            username=username,
            password=password,
            verify=verify,
        )
        with mnode_session:
            response = mnode_session.request(method=method, url=url, json=data, verify=verify, timeout=timeout)
            try:
                content = response.json()
            except json.JSONDecodeError:
                content = None
    except Exception as exc:
        module.fail_json(msg=exc.args[0], invocation=invocation)

    if response.ok:
        changed = True
    else:
        changed = False
        module.fail_json(
            msg="Non successful response.",
            content=response.text,
            status=response.status_code,
            invocation=invocation
        )

    module.exit_json(changed=changed, content=content, status=response.status_code, invocation=invocation)


def main():
    """Call mNode APIs from playbook."""
    execute_mnode_api()


if __name__ == "__main__":
    main()