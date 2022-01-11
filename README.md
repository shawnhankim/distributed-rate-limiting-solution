# Distributed Rating Limiting Solution Example w/ Echo System
The rate-limit allows you to limit the amount of HTTP requests a user can make in a given period of time.

This repo provides an example of distributed rate-limiter app that can be called by an API gateway. Given this way, developers do not need to implement rate-limit handling in each API endpoint of various apps. So you can only focus on developing business logic in your application.

```bash
User(SPA)
  |            
  |        [SPA: Frontend]
  |            |                                                        
  |            |                [RL in API-GW or different machine]             Pub
  |   [IdP]--+ |   .................................................    +----> [Sync-App 1..j]
  |          | |   :                                  Sub          :    |       1) Event
  |          | |   :            +- RL 1 --- Cache <-- Sync-App <-+ :    V       2) Regulary
[LB ] --+- [API-GW 1] -+        |     :                          +-+-> [LB] -+ 
 N+     |    N+    :   +- [LB] -+- RL n --- Cache <-- Sync-App <-+ :         +- Cache 1
        |          :   |   NGX                                     :         |        :
        |          :...+...........................................:         +- Cache k
        |              |                                                     |
        |              +- [LB] -+- UA 1 (Fake Upload App)                    +- Datastore 1
        |    N+        |   NGX  |     :                                      |            :
        +- [API-GW m] -+        +- UA i                                      |  Datastore l
             | |                                                             +- (Key/Value)
      [SPA]--+ +-- [IdP]                                                     

* RL: Rate Limiter, UA: Upload-App, LB: Load Balancer
* N+: Nginx Plus, NGX: Nginx OSS
* SPA: Single Page App, GW: Gateway, IdP: Identity Provider (Amazon Cognito)
```

## Getting Started

**Prerequisites:**
- Install Python 3.x for unit and functional test.
- Install Docker and Docker Compose for integration, end-to-end (E2E) test.
- Install Golang for integration test.
- Add `127.0.0.1 host.docker.internal` into `/etc/hosts` file.
- Add `127.0.0.1 my-rate-limiter.com` into `/etc/hosts` file.
- ]Create your certificates and copy them](https://github.com/shawnhankim/nginx-openid-connect/tree/main/docker#prepare-certs-and-nginx-plus-license) into `services/frontend-load-balancer-api-gateway-oidc/ssl` directory.
- Download the NGINX Plus license files via the [F5/NGINX customer portal](https://cs.nginx.com/?_ga=2.268586425.912746048.1620625839-85838359.1596947109), and copy the files into the following path.
  - Path: `services/frontend-load-balancer-api-gateway-oidc/ssl`
  - Files: `nginx-repo.crt`, `nginx-repo.key`
- [Set up your IdP](https://github.com/shawnhankim/nginx-openid-connect/#configuring-your-idp).


**Create and run Docker container images for `frontend-load-balancer-api-gateway-oidc`, `frontend-app`, `backend-load-balancer-to-rate-limiter`, `rate-limiter`, `backend-load-balancer-to-upload-app`, and `upload-app` :**
```bash
$ make start
``` 

**Check docker status if 9 containers are successfully run:**
```bash
$ make watch
``` 
![](./img/docker_ps_distributed_rate_limiting_system.png.png)

**Run and Test Distributed Rate-Limiting Solution:**

> Chrome
![](./img/distributed-rate_limiting_test_tool_chrome.png)

> Safari
![](./img/distributed_rate_limiting_test_tool_safari.png)
