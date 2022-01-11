/**
 * Distributed Rate Limiter Client with NGINX
 */

export default {
    decrement
}


// Rate Limiting Request: Global or User Level Quota Decrement
//
function decrement(r) {
    var uri = '/ratelimit-decrement/';
    if (!r.variables.x_user_id) {
        uri += 'global';
    } else {
        uri += 'users/' + r.variables.x_user_id;
    }
    r.subrequest(uri, function(res) {
        var body = JSON.parse(res.responseBody);
        r.variables.quota_limit           = body.quota_limit;
        r.variables.quota_remaining       = body.quota_remaining;
        r.headersOut['X-Quota-Limit']     = body.quota_limit;
        r.headersOut['X-Quota-Remaining'] = body.quota_remaining;
        if (res.status == 404) {
            r.return(500)
        } else if (res.status == 200) {
            r.return(200)
        } else {
            r.return(403)
        }
    });
}
