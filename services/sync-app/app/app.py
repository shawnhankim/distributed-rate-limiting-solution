"""Sync App"""

from flask import Flask
from flask_restx import Api, Resource
from os import environ

from core.apis.rate_limit_config import RateLimitConfig
from core.apis.rate_limit_decrement import RateLimitDecrement
from core.apis.rate_limit_status import RateLimitStatus
from core.models.rate_limit_config import (
    req_api_model as ratelimit_req_api_model,
    res_api_model as ratelimit_res_api_model
)
from core.models.rate_limit_decrement import (
    req_api_model as decrement_req_api_model,
    res_api_model as decrement_res_api_model
)
from core.common.dynamodb import RateLimitDynamoDB


# --------------------------------------------------------------------------- #
#                                                                             #
#                           -  App Initialization  -                          #
#                                                                             #
#   Create app, name space, API request/response models, API access objects:  #
#                                                                             #
#     1) control plane: rate-limit policy for administrator                   #
#        - This is not integrated with data plane yet.                        #
#                                                                             #
#     2) data plane: rate-limiter configuration and request per globa/user    #
#        - ns_config   : configuring rate-limit                               #
#        - ns_decrement: rate-limit request                                   #
#        - ns_status   : check rate-limit status                              #
#                                                                             #
# --------------------------------------------------------------------------- #

app = Flask(__name__)

api = Api(app, version='1.0', title='Rate Limiter Sync API',
          description='APIs for synchronizing quota-limit between' +
          ' rate-limiter and key/value datastore')

ns_config = api.namespace(
    'ratelimits',
    description='Rate Limit Config for Data Plane'
)
ns_decrement = api.namespace(
    'ratelimits',
    description='Rate Limit Request Per Global or User'
)
ns_status = api.namespace(
    'ratelimits/status',
    description='Rate Limiter Status for All Buckets'
)

limit_req_model = api.model('ratelimit-req', ratelimit_req_api_model())
limit_res_model = api.model('ratelimit-res', ratelimit_res_api_model())
decrement_req_model = api.model('decrement-req', decrement_req_api_model())
decrement_res_model = api.model('decrement-res', decrement_res_api_model())

dynamo_db = RateLimitDynamoDB()
dynamo_db.create_table()

config_api = RateLimitConfig(ns_config, dynamo_db)
decrement_api = RateLimitDecrement(ns_decrement, dynamo_db)
status_api = RateLimitStatus(ns_decrement, dynamo_db)


"""
View DynamoDB Local tables with DyanmoDB Admin GUI:

    $ npm install -g dynamodb-admin
    $ DYNAMO_ENDPOINT=http://localhost:8000 dynamodb-admin

Now visit http://localhost:8001 on your web browser to access the
dynamodb-admin GUI.
"""
# --------------------------------------------------------------------------- #
#                                                                             #
#                            -  Data Plane APIs  -                            #
#                                                                             #
#  Configure rate-limiter policy, and process rate-limit request:             #
#                                                                             #
#    1) Configuring rate-limit                                                #
#       - global level: configure rate-limit policy for entire system         #
#       - a user level: configure rate-limit policy per each user             #
#                                                                             #
#    2) Processing rate-limit                                                 #
#       - global level: request rate-limit for entire system                  #
#       - a user level: request rate-limit for an user                        #
#                                                                             #
#    3) Check rate-limit status                                               #
#       - all list    : check quota remaining from global/user level limiter  #
#       - global level: check quota remaining from global level limiter       #
#       - a user level: check quota remaining from user level limiter         #
#                                                                             #
#   Note:                                                                     #
#                                                                             #
#    + The APIs are called by API gateway instead of each app's biz logic     #
#      because of the following reasons:                                      #
#      - Easy to set up rate-limit policy in data-plane without implementing  #
#        the API calls per each app codes by just configuration.              #
#      - Easy to change different policies for each API endpoint.             #
#                                                                             #
# --------------------------------------------------------------------------- #


@ns_config.route('/config/global')
@ns_config.response(404, 'Unable to find a global rate-limit configuration.')
@ns_config.response(409, 'The global rate-limit is already configured.')
class GlobalRateLimitConfigAPI(Resource):
    """Rate Limit API to configure a global rate-limit policy.

    It is routed to the endpoint of '{{FQDN}}/ratelimit-config/global'.

    With this API endpoint, we can configure the global rate-limiter by calling
    the function of configure_global_limit() in the class of RateLimiter.
    """
    @ns_config.marshal_with(limit_res_model, code=200)
    def get(self):
        """Get a global rate-limiter configuration information"""
        return config_api.get()

    @ns_config.expect(limit_req_model)
    @ns_config.marshal_with(limit_res_model, code=200)
    def put(self):
        """Configure a global rate-limiter."""
        return config_api.put(api.payload)

    @ns_config.response(204, 'deleted')
    def delete(self):
        """Delete a global rate-limiter"""
        return config_api.delete()


@ns_config.route('/config/users/<string:id>')
@ns_config.response(404, 'Unable to find a user rate-limit configuration.')
@ns_config.response(409, 'The user rate-limit is already configured.')
@ns_config.param('id', 'Please enter a user ID')
class UserRateLimitConfigAPI(Resource):
    """Rate Limit API to configure a user rate-limit policy.

    It is routed to the endpoint of '{{FQDN}}/ratelimit-config/users/<int:id>'.

    With this API endpoint, we can configure the global rate-limiter by calling
    a function of configure_limit() in the class of RateLimiter. In production,
    the endpoint of /login of OIDC workflow can call this function rather than
    implementing the administrative feature to save the cost of development and
    maintenance. Additionally. we can mitigate security attacks based on using
    the OIDC integration.
    """
    @ns_config.marshal_with(limit_res_model, code=200)
    def get(self, id):
        """Get a user's rate-limiter configuration information"""
        return config_api.get(id)

    @ns_config.expect(limit_req_model)
    @ns_config.marshal_with(limit_res_model, code=200)
    def put(self, id):
        """Configure a user's rate-limiter."""
        return config_api.put(api.payload, id)

    @ns_config.response(204, 'deleted')
    def delete(self, id):
        """Delete a user's rate-limiter"""
        return config_api.delete(id)


@ns_decrement.route('/decrement/global')
@ns_decrement.response(429, 'Too many requests.')
@ns_decrement.response(404, 'Not found')
class GlobalRateLimitDecrementAPI(Resource):
    """Rate Limit API to process a global rate-limit request.

    It is routed to the endpoint of '{{FQDN}}/ratelimit-decrement/global'.

    With this API endpoint, we can request the global rate-limit by calling the
    function of process_request() in the class of RateLimiter. It returns error
    with a code of 429 which is 'too many requests' if it exceedes the maximum
    amount of quota (a.k.a. X-RateLimit-Limit).

    The fields of X-RateLimit-Limit and X-RateLimit-Remaining are set in the
    response header of api-gateway in this demo repo. The values are included
    in the response body in this app instead for testing purpose.

    IETF RateLimit Header Fields:
    https://tools.ietf.org/id/draft-polli-ratelimit-headers-00.html
    """
    @ns_decrement.marshal_with(decrement_res_model, code=429)
    @ns_decrement.marshal_with(decrement_res_model, code=200)
    def get(self):
        """Reduce the number of quota remainings globally"""
        return decrement_api.get()


@ns_decrement.route('/decrement/users/<string:id>')
@ns_decrement.response(429, 'Too many requests.')
@ns_decrement.response(404, 'Not found')
class UserRateLimitDecrementAPI(Resource):
    """Rate Limit API to process a user rate-limit request.

    It is routed to the URI of '{{FQDN}}/ratelimit-decrement/users/<int:id>'.

    The values of X-RateLimit-Limit and X-RateLimit-Remaining are set in the
    response header of api-gateway such as global rate-limiter. The values are
    included in the response body in this app instead for testing purpose.

    In production, I recommend the user ID is matched with the `sub` of IdP so
    that we can easily maintain user mgmt., and mitigate threats possibility
    by reusing IdP. In the meantime, I have changed the type of ID from integer
    to string for considering scaling millions of users.
    """
    @ns_decrement.marshal_with(decrement_res_model, code=429)
    @ns_decrement.marshal_with(decrement_res_model, code=200)
    def get(self, id):
        """Reduce the number of quota remainings per user ID"""
        return decrement_api.get(id)


@ns_status.route('')
@ns_status.response(404, 'Status not found')
class RateLimitStatusAPI(Resource):
    """Rate Limit API to list quota remaining status of global/user limiter.

    It is routed to the endpoint of '{{FQDN}}/ratelimit-status'.
    """
    @ns_status.marshal_with(decrement_res_model, code=200)
    def get(self):
        """Get list of remainig status of global/user rate-limiter"""
        return status_api.list()


@ns_status.route('/global')
@ns_status.response(404, 'Status not found')
class GlobalRateLimitStatusAPI(Resource):
    """Rate Limit API to get quota remaining status of global limiter.

    It is routed to the endpoint of '{{FQDN}}/ratelimit-status/global'.
    """
    @ns_status.marshal_with(decrement_res_model, code=200)
    def get(self):
        """Get a remainig status of global rate-limiter"""
        return status_api.get()


@ns_status.route('/users/<string:id>')
@ns_status.response(404, 'Status not found')
class UserRateLimitStatusAPI(Resource):
    """Rate Limit API to get quota remaining status of user limiter.

    It is routed to the endpoint of '{{FQDN}}/ratelimit-status/users/<int:id>'.
    """
    @ns_status.marshal_with(decrement_res_model, code=200)
    def get(self, id):
        """Get a remainig status of a user's rate-limiter"""
        return status_api.get(id)


if __name__ == '__main__':
    port = int(environ.get("SYNC_APP_PORT", 8000))
    app.run(debug=True, host='0.0.0.0', port=port)
