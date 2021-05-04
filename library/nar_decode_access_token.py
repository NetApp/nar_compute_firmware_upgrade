#!/usr/bin/python

# (c) 2020-2021 NetApp, Inc
import typing as t

from ansible.module_utils.basic import AnsibleModule
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTClaimsError, JWTError

DOCUMENTATION = """

module: nar_decode_access_token

short_description: Decode JWT token

# To be changed / removed
# extends_documentation_fragment:
# version_added:
# author:

description:
- Decode the JWT using the inputs and JWKS

options:

  auth_token:
    description:
      - The encrypted authorization access token value.
    required: True
    
  auth_jwks:
    description:
      - The jwks API response data 
    required: True

  audience:
    description:
      - The intended audience value required for JWT token decoding.
    required: True
    
  algorithms:
    description:
      - The actual algorithm used for decoding the access token using JWKS data.
    required: False
    default: RS256
    
  clock_skew_leeway:
    description:
      - The Clock Skew Amount field lets you specify up to 60 seconds of leeway for the validation of this claim.
    required: False
    default: 30
"""

EXAMPLES = """
- name: Validate access token admin rights
   nar_verify_admin_access_token:
    auth_token: token_data
    auth_jwks: jwks_data
    audience: api
    algorithms: RS256
    clock_skew_leeway: 30
"""

RETURN = """
  decoded_status:
    description:
      - The status of mode (jwt decoding) status.
    
  decoded_response:
    description:
      - The decoded response data.
"""

ACCESS_TOKEN_KEY = "auth_token"
JWKS_DATA_KEY = "auth_jwks"
AUDIENCE_KEY = "audience"
CLOCK_SKEW_LEEWAY_KEY = "clock_skew_leeway"
ALGORITHMS_KEY = "algorithms"


def validate_jwt(access_token, jwks_data, algorithms, audience, clock_skew_leeway) -> t.Tuple[dict, str]:
    """

    The JSON Web Key Set (JWKS) is a set of keys containing the public key that is used
    to verify the JSON Web Token (JWT).

    Returns:
        dict: JWT Decoded response data
        str: Reason of failure if any else empty string
    """
    try:
        claims = jwt.decode(
            access_token,
            jwks_data,
            algorithms=algorithms,
            audience=audience,
            options={"leeway": clock_skew_leeway},
        )
    except (JWTError, JWTClaimsError, ExpiredSignatureError) as exc:
        return {}, f"JWT decoding Exception occurred : {exc}"
    except Exception as exc:
        return {}, f"Exception occurred : {exc}"
    return claims, ""


def execute_api():
    argument_spec = {
        "auth_token": dict(required=True, type="str"),
        "auth_jwks": dict(required=True, type="dict"),
        "audience": dict(required=True, type="str"),
        "algorithms": dict(required=False, type="str", default="RS256"),
        "clock_skew_leeway": dict(required=False, type="int", default=30),
    }
    result_dict = dict(decoded_status=False, decoded_response={})
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    response = {}
    error_reason = ""
    access_token = module.params[ACCESS_TOKEN_KEY]
    jwks_data = module.params[JWKS_DATA_KEY]
    audience = module.params[AUDIENCE_KEY]
    algorithms = module.params[ALGORITHMS_KEY]
    clock_skew_leeway = module.params[CLOCK_SKEW_LEEWAY_KEY]

    if access_token and jwks_data:
        response, error_reason = validate_jwt(access_token, jwks_data, algorithms, audience, clock_skew_leeway)
    else:
        result_dict["error_reason"] = f"Error obtaining access_token or jwks_token responses from earlier API calls"
        module.fail_json(msg=f"Non successful response.", **result_dict)

    if response and not error_reason:
        result_dict["decoded_status"] = True
        result_dict["decoded_response"] = response
        module.exit_json(msg=f"Successful response", **result_dict)
    else:
        result_dict["error_reason"] = error_reason
        module.fail_json(msg=f"Non successful response", **result_dict)


def main():
    """Decodes JWT using the inputs and JWKS."""
    execute_api()


if __name__ == "__main__":
    main()
